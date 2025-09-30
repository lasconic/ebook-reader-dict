import re
from logging import getLogger

from wikitextprocessor import Wtp

from wikidict import parse, utils

log = getLogger(__name__)

UNWANTED_TAGS = {"a", "div", "p", "span"}
WANTED_TAGS = {"b", "/b", "i", "/i", "small", "/small"}


def sanitize(html: str) -> str:
    """
    >>> sanitize('<div class="mw-content-ltr mw-parser-output" lang="en" dir="ltr"><p><span class="form-of-definition use-with-mention"><a href="/wiki/Appendix:Glossary#abbreviation" title="Appendix:Glossary">Abbreviation</a> of <span class="form-of-definition-link"><i class="Latn mention" lang="en"><a href="/wiki/Acre#English" title="Acre">Acre</a></i></span></span>: a <a href="/wiki/state" title="state">state</a> of <span class="Latn" lang="en"><a href="/wiki/Brazil#English" title="Brazil"><b some="attr">Brazil</a></b></span>\\n</p></div>')
    'Abbreviation of <i>Acre</i>: a state of <b>Brazil</b>'
    """
    # Remove those tags
    for tag in UNWANTED_TAGS:
        html = re.sub(rf"<{tag}[^>]+>", "", html)
        html = html.replace(f"<{tag}>", "").replace(f"</{tag}>", "")

    # Clean-up attributes from those tags
    html = re.sub(r"<(b|i|small)[^>]+>", r"<\1>", html)
    # Remove unwanted categories
    html = re.sub(r"\[\[Category:[^\]]*\]\]", "", html)

    return html.strip()


def render_lua_template(word: str, wikitext: str, lang_src: str, lang_dst: str) -> str:
    source_dir = parse.get_source_dir(lang_src)
    if not (input_file := parse.get_latest_xml_file(source_dir)):
        log.error("No dump found. Run with --download first ... ")
        return ""

    snapshot = input_file.stem.split("-")[-1]
    db_path = parse.get_output_file_modules(source_dir, lang_src, lang_dst, snapshot)
    ctx = Wtp(db_path, lang_code=lang_src, project="wiktionary")
    ctx.start_page(word)
    p = ctx.expand(wikitext)
    p = sanitize(p)
    p = utils.clean(p)
    return p
