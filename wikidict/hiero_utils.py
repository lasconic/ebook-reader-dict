import re
from typing import List
from .hiero import wh_phonemes, wh_files, wh_prefabs


class HieroTokenizer:

    delimiters: List[str] = []
    tokenDelimiters: List[str] = []

    singleChars: List[str] = []

    text: str = ""
    blocks: List[List[str]] = []

    currentBlock: List[str]
    token: str = ""

    def __init__(self, text: str):
        self.text = text
        self.initStatic()

    def initStatic(self) -> None:
        if self.delimiters:
            return

        self.delimiters = [" ", "-", "\t", "\n", "\r"]
        self.tokenDelimiters = ["*", ":", "(", ")"]
        self.singleChars = ["!"]

    # Split text into blocks, then split blocks into items
    def tokenize(self) -> List[List[str]]:
        if self.blocks:
            self.blocks

        self.blocks = []
        self.currentBlock = []
        self.token = ""

        # remove HTML comments
        text = re.sub(r"<!--(?:.+-->)?", "", self.text)

        for i in range(0, len(text)):
            char = text[i]
            if char in self.delimiters:
                self.newBlock()
            elif char in self.singleChars:
                self.singleCharBlock(char)
            elif char == ".":
                self.dot()
            elif char in self.tokenDelimiters:
                self.newToken(char)
            else:
                self.char(char)

        # flush stuff being processed
        self.newBlock()

        return self.blocks

    # Handles a block delimiter
    def newBlock(self) -> None:
        self.newToken()
        if self.currentBlock:
            self.blocks.append(self.currentBlock)
            self.currentBlock = []

    # Flushes current token, optionally adds another one
    # @param string|bool token token to add or false
    def newToken(self, token: str = "") -> None:
        if self.token:
            self.currentBlock.append(self.token)
            self.token = ""

        if token:
            self.currentBlock.append(token)

    # Adds a block consisting of one character
    # @param string char block character
    def singleCharBlock(self, char: str) -> None:
        self.newBlock()
        self.blocks.append([char])

    # Handles void blocks represented by dots
    def dot(self) -> None:
        if self.token == ".":
            self.token = ".."
            self.newBlock()
        else:
            self.newBlock()
            self.token = "."

    # Adds a miscellaneous character to current token
    # @param string char character to add
    def char(self, char: str) -> None:
        if self.token == ".":
            self.newBlock()
            self.token = char
        else:
            self.token += char


TABLE_START = '<table class="mw-hiero-table">'
DEFAULT_SCALE = -1
CARTOUCHE_WIDTH = 2
IMAGE_MARGIN = 1
MAX_HEIGHT = 44


def extractCode(glyph):
    return re.sub("\\\\.*$", "", glyph)


def renderGlyph(code: str) -> str:
    return ""


# Resize a glyph
#
# @param string $item glyph code
# @param bool $is_cartouche true if glyph is inside a cartouche
# @param int $total total size of a group for multi-glyph block
# @return int size
def resizeGlyph(item: str, is_cartouche: bool = False, total: int = 0) -> int:
    item = extractCode(item)
    if item in wh_phonemes:
        glyph = wh_phonemes[item]
    else:
        glyph = item

    margin = 2 * IMAGE_MARGIN
    if is_cartouche:
        margin += 2 * CARTOUCHE_WIDTH

    if glyph in wh_files:
        height = margin + wh_files[glyph][1]
        if total:
            if total > MAX_HEIGHT:
                return int(height * MAX_HEIGHT / total) - margin
            else:
                return height - margin

        else:
            if height > MAX_HEIGHT:
                return int(MAX_HEIGHT * MAX_HEIGHT / height) - margin
            else:
                return height - margin

    return MAX_HEIGHT - margin


def render(hiero: str) -> str:

    html = ""

    tokenizer = HieroTokenizer(hiero)
    blocks = tokenizer.tokenize()
    contentHtml = tableHtml = tableContentHtml = ""
    is_cartouche = False

    # ------------------------------------------------------------------------
    # Loop into all blocks
    for code in blocks:
        # simplest case, the block contain only 1 code . render
        if len(code) == 1:
            if code[0] == "!":
                # end of line
                tableHtml = "</tr></table>" + TABLE_START + "<tr>\n"

            elif "<" in code[0]:
                # start cartouche
                contentHtml += "<td>" + renderGlyph(code[0]) + "</td>"
                is_cartouche = True
                contentHtml += f'<td>{TABLE_START}<tr><td class="mw-hiero-box" style="height:{CARTOUCHE_WIDTH}px"></td></tr><tr><td>{TABLE_START}<tr>'

            elif ">" in code[0]:
                # end cartouche
                contentHtml += f'</tr></table></td></tr><tr><td class="mw-hiero-box" style="height:{CARTOUCHE_WIDTH}px"></td></tr></table></td>'
                is_cartouche = False
                contentHtml += "<td>" + renderGlyph(code[0]) + "</td>"

            elif code[0] != "":
                # assume it's a glyph or '..' or '.'
                contentHtml += (
                    "<td>"
                    + renderGlyph(code[0], resizeGlyph(code[0], is_cartouche))
                    + "</td>"
                )

        # block contains more than 1 glyph
        else:
            # convert all codes into '&' to test prefabs glyph
            prefabs = ""
            for t in code:
                if re.search("[*:!()]", t[0]):
                    prefabs += "&"
                else:
                    prefabs += t

            # test if block exists in the prefabs list
            if prefabs in wh_prefabs:
                contentHtml += (
                    "<td>"
                    + renderGlyph(prefabs, resizeGlyph(prefabs, is_cartouche))
                    + "</td>"
                )

            # block must be manually computed
            else:
                # get block total height
                line_max = 0
                total = 0
                height = 0

                for t in code:
                    if t == ":":
                        if height > line_max:
                            line_max = height

                        total += line_max
                        line_max = 0

                    elif t == "*":
                        if height > line_max:
                            line_max = height

                    else:
                        if t in wh_phonemes:
                            glyph = wh_phonemes[t]
                        else:
                            glyph = t

                        if glyph in wh_files:
                            height = 2 + wh_files[glyph][1]

                if height > line_max:
                    line_max = height

                total += line_max

                # render all glyph into the block
                block = ""
                for t in code:
                    if t == ":":
                        block += "<br />"

                    elif t == "*":
                        block += " "

                    else:
                        # resize the glyph according to the block total height
                        block += renderGlyph(t, resizeGlyph(t, is_cartouche, total))

                contentHtml += "<td>" + block + "</td>"

            contentHtml += "\n"

        if len(contentHtml) > 0:
            tableContentHtml += tableHtml + contentHtml
            contentHtml = tableHtml = ""

    if len(tableContentHtml) > 0:
        html += f"{TABLE_START}<tr>\n{tableContentHtml}</tr></table>"

    return f'<table class="mw-hiero-table mw-hiero-outer" dir="ltr"><tr><td>\n{html}\n</td></tr></table>'
