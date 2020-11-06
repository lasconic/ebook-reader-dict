"""Catalan language."""

from typing import Tuple

# Regex to find the pronunciation
pronunciation = r"{ca-pron\|(?:or=)?/([^/\|]+)"

# Regex to find the genre
genre = r"{ca-\w+\|([fm]+)"

# Float number separator
float_separator = ","

# Thousads separator
thousands_separator = "."

# Markers for sections that contain interesting text to analyse.
head_sections = ("{{-ca-}}", "{{-mul-}}")
etyl_section = ["{{-etimologia-", "{{etim-lang"]
l_sections = [
    "Abreviatura",
    "Acrònim",
    "Adjectiu",
    "Adverbi",
    "Article",
    "Contracció",
    "Infix",
    "Interjecció",
    "Lletra",
    "Nom",
    "Numeral",
    "Prefix",
    "Preposició",
    "Pronom",
    "Sigles",
    "Sufix",
    "Símbol",
    "Verb",
    *etyl_section
]

sections = tuple(l_sections)

# Some definitions are not good to keep (plural, genre, ... )
definitions_to_ignore = (
    # Ignore conjuged verbs
    "ca-forma-conj",
    # Proper nouns
    "cognom",
    "prenom",
    # Ignore genres
    "forma-f",
    # Ignore plurals
    "forma-p",
)

# Templates to ignore: the text will be deleted.
templates_ignored = (
    "manquen accepcions",
    "sense accepcions",
    "-etimologia-",
)

# Templates that will be completed/replaced using italic style.
templates_italic = {
    "alguerès-verb": "alguerès",
    "arcaic": "arcaisme",
    "fruits": "botànica",
    "plantes": "botànica",
    "valencià-verb": "valencià",
}

# Templates more complex to manage.
templates_multi = {
    # {{color|#E01010}}
    "color": "color(parts[1])",
    # {{e|la|lupus}}
    "e": "parts[2]",
    # {{forma-|abreujada|ca|bicicleta}}
    "forma-": "f\"{italic('forma ' + parts[1] + ' de')} {strong(parts[-1])}\"",
    # {{forma-a|ca|Beget}}
    "forma-a": "f\"{italic('forma alternativa de')} {strong(parts[2])}\"",
    # {{forma-pron|ca|estimar}}
    "forma-pron": "f\"{italic('forma pronominal de')} {strong(parts[2])}\"",
    # {{IPAchar|[θ]}}
    "IPAchar": "parts[-1]",
    # {{marca|ca|fruits}}
    # {{marca|ca|interrogatiu|condicional}}
    "marca": "term(lookup_italic(concat(parts, sep=', ', indexes=[2, 3, 4, 5], skip='_'), 'ca'))",
    # {{marca-nocat|ca|balear}}
    # {{marca-nocat|ca|occidental|balear}}
    "marca-nocat": "term(lookup_italic(concat(parts, sep=', ', indexes=[2, 3, 4, 5]), 'ca'))",
    # {{q|tenir bona planta}}
    "q": "term(parts[-1])",
    #{{etim-s|ca|XIV}}
    "etim-s": "'Segle ' + parts[2]",
}

# Templates that will be completed/replaced using custom style.
templates_other = {
    "m": "m.",
}

# Language names for etim-lang template
# see https://ca.wiktionary.org/wiki/Categoria:Etimologia_en_catal%C3%A0
# 50 categories at last update
language_names = {
    "de": "alemany",
    "goh": "alt alemany",
    "ber": "amazic",
    "en": "anglès",
    "xaa": "àrab andalusí",
    "ar": "àrab",
    "an": "aragonès",
    "eu": "basc",
    "rmq": "caló",
    "es": "castellà",
    "roa-oca": "català medieval",
    "cel": "cèltic",
    "da": "danès",
    "fro": "francès antic",
    "fr": "francès",
    "gl": "gallec",
    "gem": "germànic",
    "got": "gòtic",
    "grc": "grec antic",
    "he": "hebreu",
    "hbo": "hebreu antic",
    "hi": "hindi",
    "hu": "hongarès",
    "xib": "ibèric",
    "it": "italià",
    "ja": "japonès",
    "ku": "kurd",
    "la": "llatí",
    "mk": "macedoni",
    "ms": "malai",
    "nl": "neerlandès",
    "no": "noruec",
    "oc": "occità",
    "pro": "occità antic",
    "pt": "portuguès",
    "ru": "rus",
    "sa": "sànscrit",
    "sc": "sard",
    "scn": "sicilià",
    "sv": "suec",
    "th": "tai",
    "zh": "xinès",
}

def last_template_handler(template: Tuple[str, ...], locale: str) -> str:
    """
    Will be called in utils.py::transform() when all template handlers were not used.

        >>> last_template_handler(["terme", "it", "come"], "ca")
        '<i>come</i>'

    """
    from collections import defaultdict

    from .defaults import last_template_handler as default
    from ..user_functions import century, italic, term

    tpl = template[0]
    parts = list(template[1:])
    # Handle {{etim-lang}} and {{terme}} templates
    if tpl == "etim-lang":
        phrase = ""
        if parts[0] in language_names:
            if language_names[parts[0]].startswith(("a", "i", "o", "u", "h")):
                phrase += "de l'"
            else:
                phrase += "del "
            phrase += f"{language_names[parts[0]]} {italic(parts[2])}"
        return phrase
    elif tpl == "terme":
        data = defaultdict(str)
        for part in parts.copy():
            if "=" in part:
                key, value = part.split("=", 1)
                data[key] = value
                parts.pop(parts.index(part))
        phrase = ""
        if len(parts) > 2 and "=" not in parts[2]:
            phrase = f"{italic(parts[2])}"
        else:
            phrase = f"{italic(parts[1])}"
        if data['trad'] and data['trans']:
            phrase += f" ({italic(data['trans'])}, «{data['trad']}»)"
        elif data['trad']:
            phrase += f" («{data['trad']}»)"
        elif data['trans']:
            phrase += f" ({italic(data['trans'])})"
        if data['lit']:
            phrase += f" (literalment «{data['lit']}»)"
        return phrase

    return default(template, locale)

# Release content on GitHub
# https://github.com/BoboTiG/ebook-reader-dict/releases/tag/ca
release_description = """\
Les paraules compten: {words_count}
Abocador Viccionari: {dump_date}

Instal·lació:

1. Copieu el fitxer [dicthtml-{locale}.zip <sup>:floppy_disk:</sup>]({url}) a la carpeta `.kobo/dict/` del lector.
2. **Reinicieu** el lector.

<sub>Actualitzat el {creation_date}</sub>
"""

# Dictionary name that will be printed below each definition
wiktionary = "Viccionari (ɔ) {year}"
