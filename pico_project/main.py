# main.py
"""Example application integrating RTC, OLED and joystick."""
from machine import I2C, Pin
import time

from rtc_ds1307 import DS1307
from oled_display import OLEDDisplay
from joystick import Joystick


# Initialize I2C on GPIO0 (SDA) and GPIO1 (SCL)
i2c = I2C(0, scl=Pin(1), sda=Pin(0))

rtc = DS1307(i2c)
display = OLEDDisplay(i2c)
joystick = Joystick()


def main():
    while True:
        dt = rtc.read_time()
        display.show_time(dt)

        direction = joystick.direction()
        pressed = joystick.button_pressed()
        if direction != "neutral" or pressed:
            display.show_lines([
                f"Dir: {direction}",
                "Btn" if pressed else "",
            ])
            time.sleep_ms(300)
        else:
            time.sleep_ms(1000)


if __name__ == "__main__":
    main()
