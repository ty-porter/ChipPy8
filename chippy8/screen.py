import os
import sys
from chippy8.config import PIXEL_COLORS

class Screen:

    def __init__(self, width=64, height=32, symbol="██"):
        self.width  = width
        self.height = height
        self.symbol = symbol
        
        self.blank_pixel_buffer()

    def update(self):
        output = "\033[H\n"                                                  # Move the cursor to the home position, add a little border
        for pixel_row in self.pixels:
            output += "  "                                                   # Add a bit of border in case cursor causes line to wrap
            for pixel in pixel_row:
                output += "\033[38;2;{};{};{}m".format(*PIXEL_COLORS[pixel]) # Set the cell to the pixel color
                output += self.symbol                                        # Draw the pixel
                output += "\033[37m"                                         # Reset the color

            output += " \n"

        sys.stdout.write(output)

    def place_sprite(self, sprite, x, y):
        collision = 0

        for y_offset, pixel_row in enumerate(sprite):
            for x_offset, pixel in enumerate(pixel_row):
                abs_y = (y + y_offset) % self.height
                abs_x = (x + x_offset) % self.width

                current_pixel = self.pixels[abs_y][abs_x]
                self.pixels[abs_y][abs_x] = current_pixel ^ pixel
                collision = current_pixel & pixel

        self.update()

        return collision

    def clear_screen(self):
        self.blank_pixel_buffer()

    def load_emulator_window(self):
        os.system('cls||clear')
        os.system('mode con: cols={} lines={}'.format(self.width * 2 + 5, self.height + 3))

    def blank_pixel_buffer(self):
        self.pixels = [[0 for _ in range(self.width)] for _ in range(self.height)]