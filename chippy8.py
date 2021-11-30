import argparse
from os.path import exists

from chippy8.cpu import CPU as ChipPy8
from chippy8.screen import Screen
from chippy8.config import FONT_FILE


parser = argparse.ArgumentParser(description='A Python CHIP-8 Emulator.')
parser.add_argument('filepath', metavar='F', type=str, help='path to the CHIP-8 ROM')
args = parser.parse_args()

def run():
    chippy.screen.load_emulator_window()

    while True:
        chippy.delay()
        chippy.execute_instruction()

if __name__ == '__main__':
    screen = Screen()
    chippy = ChipPy8(screen)

    chippy.load_rom(FONT_FILE, 0)

    if exists(args.filepath):
        chippy.load_rom(args.filepath)
        run()
    else:
        print("Couldn't load ROM at {}! Check your file path and try again.".format(args.filepath))
