# oled_display.py
"""Helper class for SSD1306 OLED display."""
from machine import I2C
import ssd1306


class OLEDDisplay:
    """Wrapper around ``ssd1306`` for convenience."""

    def __init__(self, i2c: I2C, width: int = 128, height: int = 64):
        self.oled = ssd1306.SSD1306_I2C(width, height, i2c)
        self.width = width
        self.height = height

    def show_lines(self, lines):
        """Display multiple lines of text."""
        self.oled.fill(0)
        for i, text in enumerate(lines):
            self.oled.text(str(text), 0, i * 10)
        self.oled.show()

    def show_time(self, datetime_tuple):
        """Convenience method to display time and date."""
        if not datetime_tuple:
            self.show_lines(["RTC Error"])
            return

        year, month, day, _, hour, minute, second, _ = datetime_tuple
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
        self.show_lines([date_str, time_str])
