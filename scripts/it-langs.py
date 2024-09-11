from typing import Dict

from scripts_utils import get_htmlparser

ROOT = "https://it.wiktionary.org"
START_URL = f"{ROOT}/wiki/Categoria:Template_lingua_testo"
NEXTPAGE_TEXT = "pagina successiva"


def process_page(url: str, results: Dict[str, str]) -> str:
    parser = get_htmlparser(url)

    nextpage = ""
    nextpage_div = parser.css_first("#mw-pages")
    last_link = nextpage_div.css("a")[-1]
    if NEXTPAGE_TEXT == last_link.text():
        nextpage = ROOT + last_link.attributes.get("href")

    content_div = parser.css_first("div.mw-category-generated")
    lis = content_div.css("li")
    for li in lis:
        try:
            tpl_name = li.text().split(":")[1]
        except IndexError:
            continue
        tpl_url = ROOT + li.css_first("a").attributes.get("href")
        tpl_parser = get_htmlparser(tpl_url)
        lang = tpl_parser.css_first("div.mw-parser-output").css_first("a").text()
        results[tpl_name] = lang
    return nextpage


results: Dict[str, str] = {}

next_page_url = START_URL
while next_page_url:
    next_page_url = process_page(next_page_url, results)

print("langs = {")
for key, value in sorted(results.items()):
    print(f'    "{key}": "{value}",')
print(f"}}  # {len(results):,}")
