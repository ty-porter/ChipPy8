from chippy8.config import KEY_MAPPING
from pynput.keyboard import Listener

class Keyboard:
    def __init__(self):
        self.current_key = None
        self.start_listening()

    def start_listening(self):
        self.listener = Listener(
            on_press   = self.on_press, 
            on_release = self.on_release
        )
        self.listener.start()

    def on_press(self, key):
        self.current_key = key

    def on_release(self, _key):
        self.current_key = None

    def is_pressed(self, value):
        return self.mapped_key_value() == value

    def mapped_key_value(self):
        try:
            key_code = self.current_key.value.vk

            return KEY_MAPPING[key_code].value.vk
        except (AttributeError, KeyError):
            return -1