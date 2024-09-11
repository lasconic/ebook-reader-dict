from scripts_utils import get_htmlparser

ROOT = "https://en.wiktionary.org"


def get_text(url: str) -> str:
    parser = get_htmlparser(url)
    div = parser.css_first("span.form-of-definition")
    if not div:
        return ""
    res = str(div.text()).replace(" term", "")
    return res.replace(" [Term?]", "")


def print_aliases(template: str, text: str, dot: bool) -> int:
    count = 0
    url_template = f"{ROOT}/wiki/Special:WhatLinksHere?target=Template%3A{template}&namespace=&hidetrans=1&hidelinks=1"
    parser = get_htmlparser(url_template)
    if ul := parser.css_first("ul#mw-whatlinkshere-list"):
        for li in ul.css("li"):
            alias = li.css_first("a").text().split(":")[1]
            print(f'    "{alias}": {{')
            print(f'        "text": "{text}",')
            print(f'        "dot": {tds["dot"] == "yes"},')
            print("    },")
            count += 1
    return count


url = f"{ROOT}/wiki/Category:Form-of_templates"
parser = get_htmlparser(url)
table = parser.css_first("div.mw-parser-output > table")

columns = ["template", "aliases", "cat", "inflection", "cap", "dot", "from", "pos"]

body = table.css_first("tbody")
trs = body.css("tr")
trs.pop(0)  # remove header
count = 0
print("form_of_templates = {")
for tr in trs:
    tds_html = tr.css("td")
    tds0 = [t.text().strip() for t in tds_html]
    if tds := dict(zip(columns, tds0)):
        link = tr.css_first("a")
        url_template = ROOT + link.attributes["href"]
        if text := get_text(url_template):
            print(f'    "{tds["template"]}": {{')
            print(f'        "text": "{text}",')
            print(f'        "dot": {tds["dot"] == "yes"},')
            print("    },")
            count += 1
            count += print_aliases(tds["template"], text, tds["dot"] == "yes")


print(f"}}  # {count:,}")
