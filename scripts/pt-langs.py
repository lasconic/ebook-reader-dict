from typing import Dict

from scripts_utils import get_htmlparser

ROOT_URL = "https://pt.wiktionary.org"
START_URL = f"{ROOT_URL}/wiki/Categoria:!Predefinição_ISO_639"
NEXTPAGE_TEXT = "página seguinte"


def process_page(page_url: str, languages: Dict[str, str]) -> str:
    parser = get_htmlparser(page_url)

    nextpage = ""
    nextpage_div = parser.css_first("#mw-pages")
    last_link = nextpage_div.css("a")[-1]
    if NEXTPAGE_TEXT == last_link.text():
        nextpage = ROOT_URL + last_link.attributes.get("href")

    content = nextpage_div.css_first("div.mw-category")
    lis = content.css("li")
    for li in lis:
        link = li.css_first("a").attributes["href"]
        li_url = ROOT_URL + link
        key = li.text().split(":")[1]
        if sub_parser := get_htmlparser(li_url):
            if content := sub_parser.css_first("div.mw-parser-output > p"):
                value = content.text()
                if value_html := content.css_first("b"):
                    value = value_html.text()
                languages[key] = value.strip()
    return nextpage


next_page_url = START_URL
languages: Dict[str, str] = {}

while next_page_url:
    next_page_url = process_page(next_page_url, languages)

assert len(languages)
print("langs = {")
for key, value in sorted(languages.items()):
    print(f'    "{key}": "{value}",')
print(f"}}  # {len(languages):,}")
