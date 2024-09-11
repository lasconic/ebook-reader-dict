from typing import Dict

from scripts_utils import get_htmlparser

ROOT_URL = "https://de.wiktionary.org"
START_URL = f"{ROOT_URL}/wiki/Kategorie:Wiktionary:Sprachk%C3%BCrzel"
NEXTPAGE_TEXT = "nächste Seite"

ALIAS_URL = "https://de.wiktionary.org/w/index.php?title=Spezial:Linkliste/{}&hidetrans=1&hidelinks=1"


def process_page(page_url: str, languages: Dict[str, str]) -> str:
    parser = get_htmlparser(page_url)

    nextpage = ""
    nextpage_div = parser.css_first("#mw-pages")
    last_link = nextpage_div.css("a")[-1]
    if NEXTPAGE_TEXT == last_link.text():
        nextpage = ROOT_URL + last_link.attributes["href"]

    content = parser.css_first("div.mw-category")
    lis = content.css("li")
    for li in lis:
        link = li.css_first("a").attributes["href"]
        li_url = ROOT_URL + link
        key = li.text().split(":")[1]
        sub_parser = get_htmlparser(li_url)
        content = sub_parser.css_first("div.mw-parser-output > p")
        value = content.text().strip()
        languages[key] = value
        a_url = ALIAS_URL.format(li.text())
        parser_alias = get_htmlparser(a_url)
        if ul_alias := parser_alias.css_first("ul#mw-whatlinkshere-list"):
            for alias_li in ul_alias.css("li"):
                alias_text = alias_li.css_first("a").text()
                alias_key = alias_text.split(":")[1]
                languages[alias_key] = value

    return nextpage


next_page_url = START_URL
languages: Dict[str, str] = {}

while next_page_url:
    next_page_url = process_page(next_page_url, languages)


print("langs = {")
for key, value in sorted(languages.items()):
    print(f'    "{key}": "{value}",')
print(f"}}  # {len(languages):,}")
