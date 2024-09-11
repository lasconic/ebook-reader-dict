from typing import Dict

from scripts_utils import get_htmlparser

START_URL = "https://es.wiktionary.org/wiki/Categor%C3%ADa:Plantillas_de_campo_sem%C3%A1ntico"
ROOT_URL = "https://es.wiktionary.org/"
ALIAS_URL = "https://es.wiktionary.org/w/index.php?title=Especial:LoQueEnlazaAqu%C3%AD/{}&hidetrans=1&hidelinks=1"
NEXTPAGE_TEXT = "página siguiente"


def process_alias_page(model: str, template_text: str, results: Dict[str, str]) -> None:
    url = ALIAS_URL.format(model)
    parser = get_htmlparser(url)
    ul = parser.css_first("ul#mw-whatlinkshere-list")
    if not ul:
        return
    for alias in ul.css("a.mw-redirect"):
        alias = alias.text().replace("Plantilla:", "")
        if alias == "editar":
            continue
        results[alias] = template_text


def process_cs_page(url: str, results: Dict[str, str]) -> str:
    parser = get_htmlparser(url)

    nextpage = ""
    nextpage_div = parser.css_first("#mw-pages")
    last_link = nextpage_div.css("a")[-1]
    if NEXTPAGE_TEXT == last_link.text():
        nextpage = ROOT_URL + last_link.attributes["href"]

    divs_category = parser.css("div.mw-category-group")
    for divs_category in divs_category:
        lis = divs_category.css("li")
        for li in lis:
            template_link = li.css_first("a")
            template_url = ROOT_URL + template_link.attributes["href"]
            template_name = template_link.text().split(":")[1]
            template_parser = get_htmlparser(template_url)
            template_text_div = template_parser.css_first("div.mw-parser-output")
            template_text = template_text_div.css_first("p").text().strip()
            if template_text[-1] == ".":
                template_text = template_text[:-1]
            results[template_name] = template_text
            process_alias_page(template_link.text(), template_text, results)

    return nextpage


results: Dict[str, str] = {}
next_page_url = START_URL
while next_page_url:
    next_page_url = process_cs_page(next_page_url, results)


print("campos_semanticos = {")
for t, r in sorted(results.items()):
    print(f'    "{t}": "{r}",')
print(f"}}  # {len(results):,}")
