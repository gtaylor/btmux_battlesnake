"""
ANSI escape sequences and utils.
"""

import re

ANSI_NORMAL = "%cn"

ANSI_UNDERLINE = "%cu"
ANSI_HILITE = "%ch"
ANSI_INVERSE = "%ci"
ANSI_INV_HILITE = "%ci%ch"

# Foreground colors
ANSI_BLACK = "%cx"
ANSI_HI_BLACK = ANSI_HILITE + ANSI_BLACK
ANSI_RED = "%cr"
ANSI_HI_RED = ANSI_HILITE + ANSI_RED
ANSI_GREEN = "%cg"
ANSI_HI_GREEN = ANSI_HILITE + ANSI_GREEN
ANSI_YELLOW = "%cy"
ANSI_HI_YELLOW = ANSI_HILITE + ANSI_YELLOW
ANSI_BLUE = "%cb"
ANSI_HI_BLUE = ANSI_HILITE + ANSI_BLUE
ANSI_MAGENTA = "%cm"
ANSI_HI_MAGENTA = ANSI_HILITE + ANSI_MAGENTA
ANSI_CYAN = "%cc"
ANSI_HI_CYAN = ANSI_HILITE + ANSI_CYAN
ANSI_WHITE = "%cw"
ANSI_HI_WHITE = ANSI_HILITE + ANSI_WHITE

# Background colors
ANSI_BACK_BLACK = "%cX"
ANSI_BACK_RED = "%cR"
ANSI_BACK_GREEN = "%cG"
ANSI_BACK_YELLOW = "%cY"
ANSI_BACK_BLUE = "%cB"
ANSI_BACK_MAGENTA = "%cM"
ANSI_BACK_CYAN = "%cC"
ANSI_BACK_WHITE = "%cW"

# Formatting Characters
ANSI_RETURN = "%r"
ANSI_TAB = "%t"
ANSI_SPACE = "%b"

RE_ANSI_ESCAPES = re.compile(r'%c[fihnxrgybmcwFIHNXRGYBMCW]')


def remove_ansi_codes(colored_text):
    """
    Removes all %c color codes.

    :param str colored_text: The original text that may include color codes.
    :rtype: str
    :returns: The text, minus color codes.
    """

    return RE_ANSI_ESCAPES.sub('', colored_text)
