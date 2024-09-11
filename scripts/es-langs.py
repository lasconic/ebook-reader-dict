from scripts_utils import get_htmlparser

url = "https://es.wiktionary.org/wiki/Ap%C3%A9ndice:C%C3%B3digos_de_idioma"
soup = get_htmlparser(url)

langs = {}
tables = soup.css("table.wikitable")
for table in tables:
    if table.attributes.get("style"):
        continue
    trs = table.css("tr")
    for tr in trs:
        tds = tr.css("td")
        if len(tds) > 1:
            langs[tds[0].text().strip()] = tds[1].text().strip()

assert langs
print("langs = {")
for t, r in sorted(langs.items()):
    print(f'    "{t}": "{r}",')
print(f"}}  # {len(langs):,}")

print()
