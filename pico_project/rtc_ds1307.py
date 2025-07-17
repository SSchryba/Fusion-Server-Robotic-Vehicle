# rtc_ds1307.py
"""Driver for the DS1307 real-time clock using I2C."""
from machine import I2C


class DS1307:
    """Minimal DS1307 RTC driver."""

    def __init__(self, i2c: I2C, address: int = 0x68):
        self.i2c = i2c
        self.address = address

    @staticmethod
    def _bcd2dec(bcd: int) -> int:
        return (bcd // 16) * 10 + (bcd % 16)

    @staticmethod
    def _dec2bcd(dec: int) -> int:
        return (dec // 10) * 16 + (dec % 10)

    def read_time(self):
        """Read current time from the RTC.

        Returns a tuple compatible with ``machine.RTC().datetime()`` or
        ``None`` on error.
        """
        try:
            data = self.i2c.readfrom_mem(self.address, 0x00, 7)
        except OSError:
            return None

        second = self._bcd2dec(data[0] & 0x7F)  # remove CH bit
        minute = self._bcd2dec(data[1])
        hour = self._bcd2dec(data[2])
        wday = self._bcd2dec(data[3])
        day = self._bcd2dec(data[4])
        month = self._bcd2dec(data[5])
        year = self._bcd2dec(data[6]) + 2000
        return (year, month, day, wday, hour, minute, second, 0)

    def set_time(self, datetime_tuple):
        """Set the RTC time from a ``datetime`` tuple."""
        try:
            year, month, day, wday, hour, minute, second = datetime_tuple[:7]
            data = bytearray(
                [
                    self._dec2bcd(second),
                    self._dec2bcd(minute),
                    self._dec2bcd(hour),
                    self._dec2bcd(wday),
                    self._dec2bcd(day),
                    self._dec2bcd(month),
                    self._dec2bcd(year - 2000),
                ]
            )
            self.i2c.writeto_mem(self.address, 0x00, data)
        except OSError:
            return False
        return True
