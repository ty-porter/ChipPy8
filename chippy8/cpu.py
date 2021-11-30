from random import randint
from time import sleep
from chippy8.keyboard import Keyboard
from chippy8.config import (
    DELAY_TIME_MS,
    MAX_MEM0RY,
    PROGRAM_COUNTER_START,
    REGISTER_COUNT,
    STACK_POINTER_START
)

class CPU:

    def __init__(self, screen):
        # Initialize registers and timers
        self.reset()

        self.OPERATION_LOOKUP = {
            0x0: self.opcode_0, # See opcode_0 method for subroutines
            0x1: self.opcode_1, # 1nnn - Jump to address
            0x2: self.opcode_2, # 2nnn - Jump to subroutine at address nnn
            0x3: self.opcode_3, # 3xkk - Skip if Vx == kk
            0x4: self.opcode_4, # 4xkk - Skip if Vx != kk
            0x5: self.opcode_5, # 5xy0 - Skip if Vx == Vy
            0x6: self.opcode_6, # 6xkk - Set Vx to kk
            0x7: self.opcode_7, # 7xkk - Add kk to Vx
            0x8: self.opcode_8, # See logic subroutines
            0x9: self.opcode_9, # 9xy0 - Skip if Vx != Vy
            0xA: self.opcode_A, # Annn - Set index register to nnn
            0xB: self.opcode_B, # Bnnn - Jump to V0 + nnn
            0xC: self.opcode_C, # Cxkk - Random byte AND kk, stored in Vx
            0xD: self.opcode_D, # Dxyn - Draw n sprite rows at position (Vx, Vy) beginning at i in memory
            0xE: self.opcode_E, # See opcode_E method for keyboard subroutines
            0xF: self.opcode_F, # See utility subroutines
        }

        self.LOGICAL_OPERATION_LOOKUP = {
            0x0: self.logic_opcode_0, # 8xy0 - Set Vx = Vy
            0x1: self.logic_opcode_1, # 8xy1 - Set Vx = Vx OR Vy
            0x2: self.logic_opcode_2, # 8xy2 - Set Vx = Vx AND Vy
            0x3: self.logic_opcode_3, # 8xy3 - Set Vx = Vx XOR Vy
            0x4: self.logic_opcode_4, # 8xy4 - Set Vx = Vx + Vy, VF = carry
            0x5: self.logic_opcode_5, # 8xy5 - Set Vx = Vx - Vy, VF = NOT borrow
            0x6: self.logic_opcode_6, # 8xy6 - Set Vx bitshift right 1
            0x7: self.logic_opcode_7, # 8xy7 - Set Vx = Vy - Vx, VF = NOT borrow
            0xE: self.logic_opcode_E  # 8xyE - Set Vx bitshift left 1
        }

        self.UTILITY_OPERATION_LOOKUP = {
            0x07: self.utility_opcode_07, # Fx07 - Set Vx to delay value
            0x0A: self.utility_opcode_0A, # Fx0A - Set Vx to key press (blocking)
            0x15: self.utility_opcode_15, # Fx15 - Set delay timer to Vx
            0x18: self.utility_opcode_18, # Fx18 - Set sound timer to Vx
            0x1E: self.utility_opcode_1E, # Fx1E - Increment index register by Vx
            0x29: self.utility_opcode_29, # Fx29 - Set index register to hex Vx
            0x33: self.utility_opcode_33, # Fx33 - Decode Vx into binary-coded decimal
            0x55: self.utility_opcode_55, # Fx55 - Save V0 - Vx to index through index + x
            0x65: self.utility_opcode_65  # Fx65 - Load V0 - Vx from index through index + x
        }

        self.operand = 0
        self.memory = bytearray(MAX_MEM0RY)
        self.screen = screen
        self.screen.load_emulator_window()
        self.keyboard = Keyboard()

    def opcode_0(self):
        '''
        00E0 - Clear screen
        00EE - Return from subroutine
        '''
        if self.operand == 0x00E0:
            self.screen.clear_screen()

        if self.operand == 0x00EE:
            self.registers['sp'] -= 1
            self.registers['pc'] = self.memory[self.registers['sp']] << 8
            self.registers['sp'] -= 1
            self.registers['pc'] += self.memory[self.registers['sp']]

    def opcode_1(self):
        '''
        1nnn - Jump to address nnn
        '''
        self.registers['pc'] = self.operand & 0x0FFF

    def opcode_2(self):
        '''
        2nnn - Jump to subroutine at address nnn
        '''
        self.memory[self.registers['sp']] = self.registers['pc'] & 0x00FF
        self.registers['sp'] += 1
        self.memory[self.registers['sp']] = (self.registers['pc'] & 0xFF00) >> 8
        self.registers['sp'] += 1
        self.registers['pc'] = self.operand & 0x0FFF

    def opcode_3(self):
        '''
        3xkk - Skip next instruction if Vx == kk
        '''
        register = (self.operand & 0x0F00) >> 8
        value    = self.operand & 0x00FF

        if self.registers['v'][register] == value:
            self.registers['pc'] += 2

    def opcode_4(self):
        '''
        4xkk - Skip next instruction if Vx != kk
        '''
        register = (self.operand & 0x0F00) >> 8
        value    = self.operand & 0x00FF

        if self.registers['v'][register] != value:
            self.registers['pc'] += 2

    def opcode_5(self):
        '''
        5xy0 - Skip next instruction if Vx == Vy
        '''
        register1 = (self.operand & 0x0F00) >> 8
        register2 = (self.operand & 0x00F0) >> 4

        if self.registers['v'][register1] == self.registers['v'][register2]:
            self.registers['pc'] += 2

    def opcode_6(self):
        '''
        6xkk - Set register Vx to kk
        '''
        register = (self.operand & 0x0F00) >> 8
        value    = self.operand & 0x00FF

        self.registers['v'][register] = value

    def opcode_7(self):
        '''
        7xkk - Add kk to register Vx
        '''
        register = (self.operand & 0x0F00) >> 8
        value    = self.operand & 0x00FF
        current  = self.registers['v'][register]
        target   = value + current

        self.registers['v'][register] = target % 0x100 # Constrain to (0x00, 0xFF)

    def opcode_8(self):
        secondary_opcode = self.operand & 0x000F
        self.LOGICAL_OPERATION_LOOKUP[secondary_opcode]()

    def opcode_9(self):
        '''
        9xy0 - Skip next instruction if Vx == Vy
        '''
        register1 = (self.operand & 0x0F00) >> 8
        register2 = (self.operand & 0x00F0) >> 4

        if self.registers['v'][register1] != self.registers['v'][register2]:
            self.registers['pc'] += 2

    def opcode_A(self):
        '''
        Annn - Set index register to nnn
        '''
        value = self.operand & 0x0FFF

        self.registers['i'] = value

    def opcode_B(self):
        '''
        Bnnn - Jump to V0 + nnn
        '''
        value = self.operand & 0x0FFF

        self.registers['pc'] += (value + self.registers['v'][0])

    def opcode_C(self):
        '''
        Cxkk - Random byte AND kk, stored in Vx
        '''
        register = (self.operand & 0x0F00) >> 8
        value    = (self.operand & 0x00FF) & randint(0x00, 0xFF)

        self.registers['v'][register] = value

    def opcode_D(self):
        '''
        Dxyn - Display n-byte sprite at position (Vx, Vy) starting at memory location given by index register
        '''
        # Load X position from Vx
        x_reg_value = (self.operand & 0x0F00) >> 8
        x = self.registers['v'][x_reg_value]

        # Load Y position from Vy
        y_reg_value = (self.operand & 0x00F0) >> 4
        y = self.registers['v'][y_reg_value]

        # Load the pixel size and initialize the blank sprite
        size = self.operand & 0x000F
        sprite_array = []

        # Load the pixel data into the sprite buffer
        for i in range(0, size):
            pixel_bytes = self.memory[self.registers['i'] + i]
            # Split the byte into an iterable list of 1's and 0's
            pixel_row = [int(bit) for bit in '{0:08b}'.format(pixel_bytes)]

            sprite_array.append(pixel_row)

        # Place sprite, check for collision and store result in VF
        self.registers['v'][0xF] = 0x0
        collision = self.screen.place_sprite(sprite_array, x, y)
        self.registers['v'][0xF] = collision

    def opcode_E(self):
        '''
        Ex9E - Skip next instruction if key with value of Vx is not pressed
        ExA1 - Skip next instruction if key with value of Vx is pressed

        Both functions are non-blocking
        '''
        secondary_opcode = self.operand & 0x00FF
        register = (self.operand & 0x0F00) >> 8
        value    = self.registers['v'][register]

        if secondary_opcode == 0x9E:
            if not self.keyboard.is_pressed(value):
                self.registers['pc'] += 2
        elif secondary_opcode == 0xA1:
            if self.keyboard.is_pressed(value):
                self.registers['pc'] += 2

    def opcode_F(self):
        secondary_opcode = self.operand & 0x00FF
        self.UTILITY_OPERATION_LOOKUP[secondary_opcode]()

    def logic_opcode_0(self):
        '''
        8xy0 - Set Vx = Vy
        '''
        register1 = (self.operand & 0x0F00) >> 8
        register2 = (self.operand & 0x00F0) >> 4

        self.registers['v'][register1] = self.registers['v'][register2]

    def logic_opcode_1(self):
        '''
        8xy1 - Set Vx = Vx OR Vy
        '''
        register1 = (self.operand & 0x0F00) >> 8
        register2 = (self.operand & 0x00F0) >> 4

        value1 = self.registers['v'][register1]
        value2 = self.registers['v'][register2]

        self.registers['v'][register1] = value1 | value2

    def logic_opcode_2(self):
        '''
        8xy2 - Set Vx = Vx AND Vy
        '''
        register1 = (self.operand & 0x0F00) >> 8
        register2 = (self.operand & 0x00F0) >> 4

        value1 = self.registers['v'][register1]
        value2 = self.registers['v'][register2]

        self.registers['v'][register1] = value1 & value2

    def logic_opcode_3(self):
        '''
        8xy3 - Set Vx = Vx XOR Vy
        '''
        register1 = (self.operand & 0x0F00) >> 8
        register2 = (self.operand & 0x00F0) >> 4

        value1 = self.registers['v'][register1]
        value2 = self.registers['v'][register2]

        self.registers['v'][register1] = value1 ^ value2

    def logic_opcode_4(self):
        '''
        8xy4 - Set Vx = Vx + Vy, VF = carry
        '''
        register1 = (self.operand & 0x0F00) >> 8
        register2 = (self.operand & 0x00F0) >> 4

        value1 = self.registers['v'][register1]
        value2 = self.registers['v'][register2]

        target_value = value1 + value2

        # Handle carry bit
        self.registers['v'][0xF] = 0
        if target_value > 0xFF:
            target_value = target_value % 0x100
            self.registers['v'][0xF] = 1

        self.registers['v'][register1] = target_value

    def logic_opcode_5(self):
        '''
        8xy5 - Set Vx = Vx - Vy, VF = NOT borrow
        '''
        register1 = (self.operand & 0x0F00) >> 8
        register2 = (self.operand & 0x00F0) >> 4

        value1 = self.registers['v'][register1]
        value2 = self.registers['v'][register2]

        # Handle borrow bit
        self.registers['v'][0xF] = 1
        if value2 > value1:
            target_value = (0x100 + value1) - value2
            self.registers['v'][0xF] = 0
        else:
            target_value = value1 - value2

        self.registers['v'][register1] = target_value

    def logic_opcode_6(self):
        '''
        8xy6 - Set Vx bitshift right 1
        '''
        register1 = (self.operand & 0x0F00) >> 8
        register2 = (self.operand & 0x00F0) >> 4
        value     = self.registers['v'][register1]

        self.registers['v'][0xF]       = value & 0x1
        self.registers['v'][register1] = value >> 1

    def logic_opcode_7(self):
        '''
        8xy7 - Set Vx = Vy - Vx, VF = NOT borrow
        '''
        register1 = (self.operand & 0x0F00) >> 8
        register2 = (self.operand & 0x00F0) >> 4

        value1 = self.registers['v'][register1]
        value2 = self.registers['v'][register2]

        # Handle borrow bit
        self.registers['v'][0xF] = 1
        if value1 > value2:
            target_value = (0x100 + value2) - value1
            self.registers['v'][0xF] = 0
        else:
            target_value = value2 - value1

        self.registers['v'][register1] = target_value

    def logic_opcode_E(self):
        '''
        8xyE - Set Vx bitshift left 1
        '''
        register = (self.operand & 0x0F00) >> 8
        value    = self.registers['v'][register]

        self.registers['v'][register] = (value << 1) % 0x100 # Bitshift left and handle overflows
        self.registers['v'][0xF]      = (value & 0x80) >> 7

    def utility_opcode_07(self):
        '''
        Fx07 - Set Vx to delay value
        '''
        register = (self.operand & 0x0F00) >> 8

        self.registers['v'][register] = self.timers['delay']

    def utility_opcode_0A(self):
        '''
        Fx0A - Set Vx to key press (blocking)
        '''
        register = (self.operand & 0x0F00) >> 8

        # Block until something is pressed
        while not self.keyboard.current_key:
            pass
        
        self.registers['v'][register] = self.keyboard.mapped_key_value()

    def utility_opcode_15(self):
        '''
        Fx15 - Set delay timer to Vx
        '''
        register = (self.operand & 0x0F00) >> 8

        self.timers['delay'] = self.registers['v'][register]

    def utility_opcode_18(self):
        '''
        Fx18 - Set sound timer to Vx
        '''
        register = (self.operand & 0x0F00) >> 8

        self.timers['sound'] = self.registers['v'][register]

    def utility_opcode_1E(self):
        '''
        Fx1E - Increment index register by Vx
        '''
        register = (self.operand & 0x0F00) >> 8

        self.registers['i'] += self.registers['v'][register]

    def utility_opcode_29(self):
        '''
        Fx29 - Set index register to hex Vx (font character location)
        '''
        register = (self.operand & 0x0F00) >> 8

        self.registers['i'] = self.registers['v'][register] + PROGRAM_COUNTER_START

    def utility_opcode_33(self):
        '''
        Fx33 - Decode Vx into binary-coded decimal

        Stores hundreds digit at i
        Stores tens digit at i + 1
        Stores ones digit at i + 2

        Does not increment i (remains unchanged from start of function)
        '''
        register = (self.operand & 0x0F00) >> 8
        value    = '{:3d}'.format(self.registers['v'][register])
        i        = self.registers['i']

        self.memory[i    ] = int(value[0])
        self.memory[i + 1] = int(value[1])
        self.memory[i + 2] = int(value[2])

    def utility_opcode_55(self):
        '''
        Fx55 - Save V0 - Vx to index through index + x
        '''
        value = (self.operand & 0x0F00) >> 8
        i     = self.registers['i']

        for counter in range(value + 1):
            self.memory[i + counter] = self.registers['v'][counter]

    def utility_opcode_65(self):
        '''
        Fx65 - Load V0 - Vx from index through index + x
        '''
        value = (self.operand & 0x0F00) >> 8
        i     = self.registers['i']

        for counter in range(value + 1):
            self.registers['v'][counter] = self.memory[i + counter]

    def execute_instruction(self):
        '''
        Read program memory 2 bytes at a time. Afterwards, the program counter is incremented by 2.
        '''
        
        # Read most significant byte
        self.operand = int(self.memory[self.registers['pc']])
        # Bitshift left by 8
        self.operand = self.operand << 8
        # Read least significant byte
        self.operand += int(self.memory[self.registers['pc'] + 1])
        self.registers['pc'] += 2

        # Opcode is most significant byte from our two byte operand
        opcode = (self.operand & 0xF000) >> 12
        self.OPERATION_LOOKUP[opcode]()

        return self.operand

    def reset(self):
        '''
        Reset (or initialize) registers, timers, stack pointer, and program counter.
        '''
        # Initialize index, program counter, stack pointer, and registers
        self.registers = {
            'i':   0,
            'pc':  PROGRAM_COUNTER_START,
            'sp':  STACK_POINTER_START,
            'v':   [0] * REGISTER_COUNT
        }

        # Initialize delay and sound timers
        self.timers = {
            'delay': 0,
            'sound': 0
        }

    def load_rom(self, filename, offset=PROGRAM_COUNTER_START):
        '''
        Load ROM binary from file.
        '''
        romdata = open(filename, 'rb').read()
        for index, val in enumerate(romdata):
            self.memory[offset + index] = val

    def delay(self):
        sleep(DELAY_TIME_MS / 1000.0)

    def decrement_timers(self):
        '''
        Decrement the delay and sound timers.
        '''

        for timer in self.timers.keys():
            if self.timers[timer] != 0:
                self.timers[timer] -= 1

    def __str__(self):
        val = 'PC: {:4X}  OP: {:4X}\n'.format(
            self.registers['pc'] - 2, self.operand)

        for i in range(REGISTER_COUNT):
            val += 'V{:X}: {:2X}\n'.format(i, self.registers['v'][i])
        val += 'I: {:4X}\n'.format(self.registers['i'])

        return val