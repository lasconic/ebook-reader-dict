from typing import Dict

from scripts_utils import get_htmlparser

ROOT = "https://fr.wiktionary.org"
START_URL = "https://fr.wiktionary.org/wiki/Cat%C3%A9gorie:Mod%C3%A8les_de_th%C3%A9matique"
NEXTPAGE_TEXT = "page suivante"
ALIAS_URL = "https://fr.wiktionary.org/w/index.php?title=Sp%C3%A9cial:Pages_li%C3%A9es/Mod%C3%A8le:{}&limit=10&hidetrans=1&hidelinks=1"  # noqa


def process_category_page(url: str, results: Dict[str, str]) -> str:
    parser = get_htmlparser(url)

    nextpage = ""
    nextpage_div = parser.css_first("#mw-pages")
    last_link = nextpage_div.css("a")[-1]
    if NEXTPAGE_TEXT == last_link.text():
        nextpage = ROOT + last_link.attributes.get("href")

    content_div = parser.css_first("div.mw-category-generated")
    lis = content_div.css("li")
    for li in lis:
        template_url = ROOT + li.css_first("a").attributes.get("href")
        template_name = li.text().split(":")[1]
        template_parser = get_htmlparser(template_url)
        parser_output = template_parser.css_first("span.term, span.texte")
        rendering = parser_output.text()
        if template_name and rendering:
            results[template_name] = rendering.strip("()")

    return nextpage


def process_alias_page(key: str, value: str, results: Dict[str, str]) -> None:
    url = ALIAS_URL.format(key)
    parser = get_htmlparser(url)
    ul = parser.css_first("ul#mw-whatlinkshere-list")
    if not ul:
        return
    for alias in ul.css("a.mw-redirect"):
        alias = alias.text().replace("Modèle:", "")
        if alias == "modifier":
            continue
        results[alias] = value


next_page_url = START_URL
results: Dict[str, str] = {}

while next_page_url:
    next_page_url = process_category_page(next_page_url, results)

# Fetch aliases
for key, value in list(results.items()):
    process_alias_page(key, value, results)

print("domain_templates = {")
for t, r in sorted(results.items()):
    print(f'    "{t}": "{r}",')
print(f"}}  # {len(results):,}")
