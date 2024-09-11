from scripts_utils import get_htmlparser

root_url = "https://de.wiktionary.org"
start_url = f"{root_url}/wiki/Kategorie:Wiktionary:Sprachadjektive"
alias_url = "https://de.wiktionary.org/w/index.php?title=Spezial:Linkliste/{}&hidetrans=1&hidelinks=1"
parser = get_htmlparser(start_url)

content = parser.css_first("div .mw-category")
lis = content.css("li")
languages = {}
for li in lis:
    link = li.css_first("a").attributes["href"]
    li_url = root_url + link
    key = li.text().split(":")[1]
    sub_parser = get_htmlparser(li_url)
    content = sub_parser.css_first("div.mw-parser-output").css_first("p")
    value = content.text().strip()
    languages[key] = value
    a_url = alias_url.format(li.text())
    parser_alias = get_htmlparser(a_url)
    if ul_alias := parser_alias.css_first("ul#mw-whatlinkshere-list"):
        for alias_li in ul_alias.css("li"):
            alias_text = alias_li.css_first("a").text()
            alias_key = alias_text.split(":")[1]
            languages[alias_key] = value


print("lang_adjs = {")
for key, value in sorted(languages.items()):
    print(f'    "{key}": "{value}",')
print(f"}}  # {len(languages):,}")
