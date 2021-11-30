import os
from pynput.keyboard import KeyCode

MAX_MEM0RY            = 0x1000 # 4096
PROGRAM_COUNTER_START = 0x200
REGISTER_COUNT        = 0x10   # 16
STACK_POINTER_START   = 0x52

DELAY_TIME_MS         = 10.0
FONT_FILE             = os.path.join('chippy8', 'chippy8.font')

PIXEL_COLORS = {
    0x00: (  0,   0,   0), # BLACK (off)
    0x01: (  0, 255,   0)  # GREEN (on)
}

# Key Mapping Diagram
#
# ORIGINAL                EMULATED
# -----------------       -----------------
# | 1 | 2 | 3 | C |       | 1 | 2 | 3 | 4 |
# | 4 | 5 | 6 | D |  --\  | Q | W | E | R |
# | 7 | 8 | 9 | E |  --/  | A | S | D | F |
# | A | 0 | B | F |       | Z | X | C | V |
# -----------------       -----------------
KEY_MAPPING = {
    # First Row
    0x1: KeyCode.from_char('1'),
    0x2: KeyCode.from_char('2'),
    0x3: KeyCode.from_char('3'),
    0xC: KeyCode.from_char('4'),

    # Second Row
    0x4: KeyCode.from_char('q'),
    0x5: KeyCode.from_char('w'),
    0x6: KeyCode.from_char('e'),
    0xD: KeyCode.from_char('r'),

    # Third Row
    0x7: KeyCode.from_char('a'),
    0x8: KeyCode.from_char('s'),
    0x9: KeyCode.from_char('d'),
    0xE: KeyCode.from_char('f'),

    # Fourth Row
    0xA: KeyCode.from_char('z'),
    0x0: KeyCode.from_char('x'),
    0xB: KeyCode.from_char('c'),
    0xF: KeyCode.from_char('v')
}