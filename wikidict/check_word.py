"""Get and render a word; then compare with the rendering done on the Wiktionary to catch errors."""

import copy
import os
import re
import urllib.parse
from functools import partial
from threading import Lock
from time import sleep
from typing import List, Optional

import requests
from selectolax.lexbor import LexborHTMLParser
from requests.exceptions import RequestException

from .render import MISSING_TPL_SEEN, parse_word
from .stubs import Word
from .user_functions import color, int_to_roman
from .utils import get_random_word

# Remove all kind of spaces and some unicode characters
_replace_noisy_chars = re.compile(r"[\s\u200b\u200e]").sub
no_spaces = partial(_replace_noisy_chars, "")

# Retry mechanism
MAX_RETRIES = 5  # count
SLEEP_TIME = 5  # time, seconds


def check_mute(wiktionary_text: str, parsed_html: str, category: str) -> List[str]:
    results: List[str] = []
    clean_text = get_text(parsed_html)

    # It's all good!
    if contains(clean_text, wiktionary_text):
        return results

    results.append(category + wiktionary_text)

    # Try to highlight the bad text
    pattern = clean_text[:-1].rstrip()
    while pattern:
        if not contains(pattern, wiktionary_text):
            pattern = pattern[:-1].rstrip()
            continue

        idx = len(pattern)
        results.append(f"{clean_text[:idx]}\033[31m{clean_text[idx:]}\033[0m")
        break
    else:
        # No highlight possible, just output the whole sentence
        results.append(clean_text)

    return results


def check(wiktionary_text: str, parsed_html: str, category: str) -> int:
    """Run checks and return the error count to increment."""
    results = check_mute(wiktionary_text, parsed_html, category)
    for r in results:
        print(r, flush=True)
    return len(results) // 2


def contains(pattern: str, text: str) -> bool:
    """Check if *pattern* is in *text*, with all spaces removed.
    *text* is already stripped from spaces in get_wiktionary_page().
    """
    return no_spaces(pattern) in text


def filter_html(html: str, locale: str) -> str:
    """Some parts of the Wiktionary HTML."""
    parser = LexborHTMLParser(html)

    # Filter out warnings about obsolete template models used
    for span in parser.css("span#FormattingError"):
        span.decompose()

    # Filter out Wikispecies links
    for span in parser.css("span.trad-exposant"):
        span.decompose()

    # Filter out result of <math> and <chem>
    for span in parser.css("span.mwe-math-element"):
        span.decompose()

    if locale == "ca":
        # {{sense accepcions}}
        for i in parser.css("i"):
            if i.text().startswith("a aquesta paraula li falten les accepcions"):
                # Remove the trailing dot
                i.next.replace_with(i.next.text()[1:])
                # And remove the note
                i.decompose()
        # Filter out anchors as they are ignored from templates
        for a in parser.css("a[href]"):
            if (
                a.attributes["href"].startswith("#")
                and not a.attributes["href"].startswith("#ca#")
                and a.attributes["href"] != "#ca"
                and "mw-selflink-fragment" not in a.attributes.get("class", [])
            ):
                a.decompose()

    elif locale == "de":
        # <sup>☆</sup>
        for sup in parser.css("sup[string=☆]"):
            sup.decompose()
        # External links
        for small in parser.css("small.noprint"):
            small.decompose()
        # Internet Archive
        for a in parser.css("a.external"):
            if "archive.org" in a.attributes["href"]:
                a.decompose()
        # Lang link in {{Üxx5}}
        for a in parser.css("a"):
            if (sup := a.css_first("sup")) and sup.text().startswith("→"):
                a.decompose()
        # Other Wikis
        for a in parser.css("a.extiw"):
            if (
                ":Special:" not in a.attributes["title"]
                and (a_sup := a.css_first("sup"))
                and "WP" in a_sup.text()
                or ":Special:" in a.attributes["title"]
            ):
                a.decompose()
        for sup in parser.css("sup"):
            if sup.attributes.get("style", "") == "color:slategray;":
                sup.decompose()
            # Filter out anchors as they are ignored from templates
            for a in parser.css("a[href]"):
                if a.attributes["href"].startswith("#"):
                    a.decompose()
    elif locale == "el":
        for sup in parser.css("sup"):
            id = sup.attributes.get("id", "")
            if id.startswith("cite_"):
                sup.decompose()
    elif locale == "en":
        for span in parser.css("span"):
            if span.text(deep=False) == "and other forms":
                span.text(deep=False) += f' {span["title"]}'
        # other anchors
        for a in parser.css("a[href]"):
            if a.attributes["href"].lower().startswith(("#cite", "#mw")):
                a.decompose()

    elif locale == "es":
        # Replace color rectangle
        for span in parser.css("span#ColorRect"):
            for style in span["style"].split(";"):
                kv = style.strip().split(":")
                if len(kv) == 2 and kv[0] == "background":
                    span.previous_sibling.decompose()
                    span.replaceWith(color(kv[1].strip()))
        for a in parser.css("a[href]"):
            if a.attributes["href"].startswith("#cite"):
                a.decompose()
            # cita requerida
            elif a.attributes["href"] == "/wiki/Ayuda:Tutorial_(Ten_en_cuenta)#Citando_tus_fuentes":
                a.parent.parent.decompose()
        # coord output
        for span in parser.css("span.geo-multi-punct, span.geo-nondefault"):
            span.decompose()
        # external autonumber
        for a in parser.css("a[class='external autonumber']"):
            a.decompose()
        dts = parser.css("dt")
        for dt in dts:
            dt_array = dt.text().split(" ", 1)
            if len(dt_array) == 2:
                dt.string = f"{dt_array[0]} "
                # 2 Historia. --> (Historia):
                if "." in dt_array[1]:
                    dt_array_dot = dt_array[1].split(".")
                    for da in dt_array_dot[:-1]:
                        dt.string += f"({da})"
                    dt.string += f" {dt_array_dot[-1]}:"
                else:
                    # duplicate the definition to cope with both cases above
                    newdt = copy.copy(dt) #TODO
                    dt.parent.append(newdt)
                    if dd := dt.find_next_sibling("dd"):
                        dt.parent.append(copy.copy(dd))
                    # 2 Selva de Bohemia: --> Selva de Bohemia:
                    newdt.string = dt.string + dt_array[1] + ":"
                    # 2 Coloquial: --> (Coloquial):
                    dt.string += f"({dt_array[1]}):"

    elif locale == "fr":
        # Filter out refnec tags
        for span in parser.css("span#refnec"):
            if span.previous_sibling: #TODO
                span.previous_sibling.decompose()
            span.decompose()
        # Cette information a besoin d’être précisée
        for span in parser.css('span[title="Cette information a besoin d’être précisée"]'):
            span.decompose()
        # {{invisible}}
        for span in parser.css("span.invisible"):
            span.decompose()
        # — (Richelet, Dictionnaire français 1680)
        for span in parser.css("span.sources"):
            span.decompose()
        # → consulter cet ouvrage
        for a in parser.css("a[class='external text']"):
            if "consulter cet ouvrage" in a.text():
                a.decompose()
        # liens externes autres Wikis
        for a in parser.css("a.extiw"):
            # Wikispecies
            if (
                a.attributes["title"].startswith("wikispecies")
                and a.parent.next_sibling #TODO
                and "sur Wikispecies" in a.parent.next_sibling
            ):
                a.parent.next_sibling.replaceWith("")
            # Wikidata
            elif a.attributes["title"].startswith("d:") and a.next_sibling and "base de données Wikidata" in a.next_sibling:
                a.next_sibling.replaceWith("")
            # {{LienRouge|lang=en|trad=Reconstruction
            elif "Reconstruction" in a["title"]:
                a.decompose()
        # external autonumber
        for a in parser.css("a[class='external autonumber']"):
            a.decompose()
        # attention image
        for a in parser.css("a[title='alt = attention']"):
            a.replaceWith("⚠") #TODO
        # other anchors
        for a in parser.css("a[href]"):
            if a.attributes["href"].lower().startswith(("#cite", "#ref", "#voir")):
                a.decompose()

    elif locale == "it":
        # Numbered external links
        for a in parser.css("a[class='external autonumber']"):
            a.decompose()
        # Missing definitions
        for i in parser.css("i"):
            if i.text().startswith("definizione mancante"):
                i.decompose()
        # <ref>
        for a in parser.css("sup.reference"):
            a.decompose()
        # Wikispecies
        for img in parser.css("img[alt=Wikispecies]"):
            img.next_sibling.next_sibling.decompose()  # <b><a>...</a></b> TODO
            img.next_sibling.next_sibling.replaceWith(img.next_sibling.next_sibling.text[1:])  # Trailing ")"
            img.next_sibling.replaceWith("")  # space
            img.previous_sibling.replaceWith("")  # Leading "("
            img.decompose()
        # Wikipedia, Wikiquote
        for small in parser.css("small"):
            if small.css_first("a[title=Wikipedia]") or small.css_first("a[title=Wikiquote]"):
                small.decompose()

    elif locale == "pt":
        # Issue 600: remove superscript locales
        for sup in parser.css("sup"):
            if sup.css_first("a.extiw"):
                sup.decompose()
            if sup.css_first("a.new"):
                sup.decompose()
        # Almost same as previous, but for all items not elligible to be printed
        for span in parser.css("span.noprint"):
            span.decompose()
        # External links
        for small in parser.css("small"):
            if small.css_first("a.extiw"):
                small.decompose()

    elif locale == "sv":
        # <ref>
        for a in parser.css("sup.reference"):
            a.decompose()

    return no_spaces(parser.text())


def get_text(html: str) -> str:
    """Parse the HTML code and return it as a string."""
    return str(LexborHTMLParser(html).text())


def craft_url(word: str, locale: str, raw: bool = False) -> str:
    """Craft the *word* URL for the given *locale*."""
    url = f"https://{locale}.wiktionary.org/w/index.php?title={urllib.parse.quote(word)}"
    if raw:
        url += "&action=raw"
    return url


def get_url_content(url: str) -> str:
    """Fetch given *url* content with retries mechanism."""
    retry = 0
    while retry < MAX_RETRIES:
        try:
            with requests.get(url, timeout=10) as req:
                req.raise_for_status()
                return req.text
        except TimeoutError:
            sleep(SLEEP_TIME)
            retry += 1
        except RequestException as err:
            wait_time = 1
            resp = err.response
            if resp is not None:
                if resp.status_code == 429:
                    wait_time = int(resp.headers.get("retry-after") or "1")
                elif resp.status_code == 404:
                    print(err)
                    return "404"
            sleep(wait_time * SLEEP_TIME)
            retry += 1
    raise RuntimeError(f"Sorry, too many tries for {url!r}")


def get_word(word: str, locale: str) -> Word:
    """Get a *word* wikicode and parse it."""
    url = craft_url(word, locale, raw=True)
    html = get_url_content(url)
    return parse_word(word, html, locale)


def get_wiktionary_page(word: str, locale: str) -> str:
    """Get a *word* HTML."""
    url = craft_url(word, locale)
    html = get_url_content(url)
    return filter_html(html, locale)


def check_word(word: str, locale: str, lock: Optional[Lock] = None) -> int:
    errors = 0
    results: List[str] = []
    details = get_word(word, locale)
    if not details.etymology and not details.definitions:
        return errors
    text = get_wiktionary_page(word, locale)

    if details.etymology:
        for etymology in details.etymology:
            if isinstance(etymology, tuple):
                for i, sub_etymology in enumerate(etymology, 1):
                    r = check_mute(text, sub_etymology, f"\n !! Etymology {i}")  # type: ignore
                    results.extend(r)
            else:
                r = check_mute(text, etymology, "\n !! Etymology")
                results.extend(r)

    index = 1
    for definition in details.definitions:
        message = f"\n !! Definition n°{index}"
        if isinstance(definition, tuple):
            for a, subdef in zip("abcdefghijklmopqrstuvwxz", definition):
                if isinstance(subdef, tuple):
                    for rn, subsubdef in enumerate(subdef, 1):
                        r = check_mute(text, subsubdef, f"{message}.{int_to_roman(rn).lower()}")
                        results.extend(r)
                else:
                    r = check_mute(text, subdef, f"{message}.{a}")
                    results.extend(r)
        else:
            r = check_mute(text, definition, message)
            results.extend(r)
            index += 1
    # print with lock if any
    if results:
        errors = len(results) // 2
        if lock:
            lock.acquire()
        for result in results:
            print(result, flush=True)
        print(f"\n >>> [{word}] - Errors:", errors, flush=True)
        if lock:
            lock.release()

    return errors


def main(locale: str, word: str) -> int:
    """Entry point."""

    # If *word* is empty, get a random word
    word = word or get_random_word(locale)

    res = check_word(word, locale)
    return 1 if "CI" in os.environ and MISSING_TPL_SEEN else res
