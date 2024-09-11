import re
from typing import Dict

from scripts_utils import get_content, get_htmlparser

ROOT = "https://fr.wiktionary.org"
START_URL = "https://fr.wiktionary.org/wiki/Cat%C3%A9gorie:Mod%C3%A8les_de_racine_en_arabe_du_Wiktionnaire"
NEXTPAGE_TEXT = "page suivante"
RACINE_URL = "https://fr.wiktionary.org/wiki/Mod%C3%A8le:{}?action=raw"
STRIP_COMMENT = re.compile(r"<!-- \(\w+\)[^\-]+-->").sub


def process_category_page(url: str, results: Dict[str, Dict[str, str]]) -> str:
    parser = get_htmlparser(url)
    nextpage = ""
    nextpage_div = parser.css_first("#mw-pages")
    last_link = nextpage_div.css("a")[-1]
    if NEXTPAGE_TEXT == last_link.text():
        nextpage = ROOT + last_link.attributes.get("href")

    content_div = parser.css_first("#mw-pages")
    for li in content_div.css("li"):
        tpl_title = li.css_first("a").attributes.get("title")
        if " " in tpl_title or "/" in tpl_title or "ar-racine" in tpl_title:
            continue

        process_root(tpl_title.removeprefix("Modèle:"), results)

    return nextpage


def process_root(tpl: str, results: Dict[str, Dict[str, str]]) -> None:
    url = RACINE_URL.format(tpl)
    data = get_content(url)
    tpl_dict = {}
    for line in data.splitlines():
        if line.startswith(("|***", "| ***")):
            sens = line.split("=")[1].strip()
            tpl_dict["aa_sens"] = sens
        if not line.startswith("| ar-"):
            continue

        racine, text = line[1:].split("=")
        text = STRIP_COMMENT("", text.strip())
        tpl_dict[racine.strip()] = text.strip()
    if tpl_dict:
        results[tpl] = tpl_dict


next_page_url = START_URL
results: Dict[str, Dict[str, str]] = {}

while next_page_url:
    next_page_url = process_category_page(next_page_url, results)

print("racines_schemes_arabes = {")
for k, v in sorted(results.items()):
    print(f'    "{k}" : {{')
    for k1, v1 in sorted(v.items()):
        print(f'        "{k1}": "{v1}",')
    print(f"    }},  # {len(v):,}")
print(f"}}  # {len(results):,}")
