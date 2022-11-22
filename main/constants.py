import re
from enum import Enum


class HTMLTags(Enum):
    A = "a"
    ABBR = "abbr"
    ACRONYM = "acronym"
    B = "b"
    BLOCKQUOTE = "blockquote"
    CODE = "code"
    EM = "em"
    Italic = "i"
    LI = "li"
    OL = "ol"
    STRONG = "strong"
    UL = "ul"
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    H4 = "h4"
    H5 = "h5"
    H6 = "h6"
    P = "p"


ALLOWED_TAGS = [HTMLTag.value for HTMLTag in HTMLTags]
ALLOWED_TAGS_WITHOUT_HEADING = [
    HTMLTag.value for HTMLTag in HTMLTags if not re.match(r"^h\d$", HTMLTag.value)
]
