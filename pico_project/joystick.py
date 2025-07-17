# joystick.py
"""Analog joystick handler for Raspberry Pi Pico."""
from machine import ADC, Pin


class Joystick:
    """Read analog joystick direction and button press."""

    def __init__(self, x_pin=26, y_pin=27, btn_pin=22, threshold=10000):
        self.adc_x = ADC(x_pin)
        self.adc_y = ADC(y_pin)
        self.button = Pin(btn_pin, Pin.IN, Pin.PULL_UP)
        self.threshold = threshold
        self.center = 32768  # half of 16-bit range

    def read(self):
        """Return raw (x, y, button) values."""
        return (
            self.adc_x.read_u16(),
            self.adc_y.read_u16(),
            not self.button.value(),
        )

    def direction(self):
        """Return simple direction string."""
        x, y, _ = self.read()
        if x < self.center - self.threshold:
            return "left"
        if x > self.center + self.threshold:
            return "right"
        if y < self.center - self.threshold:
            return "down"
        if y > self.center + self.threshold:
            return "up"
        return "neutral"

    def button_pressed(self):
        """Return ``True`` if joystick button is pressed."""
        _, _, pressed = self.read()
        return pressed
