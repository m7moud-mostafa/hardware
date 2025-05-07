#!/usr/bin/python3
"""
imu_driver.py contains the IMUDriver class

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""

import struct
from hardware.high_level_base_driver import HighLevelBaseReceiver

class IMUDriver(HighLevelBaseReceiver):
    def receive(self):
        """
        Returns:
            Tuple[float, float, float, float, float, float] or None:
            (ax, ay, az, gx, gy, gz)
        """
        raw = self.driver.receive()
        if raw is None:
            return None

        if len(raw) < 24:
            raise MsgLengthError("The imu msg should be 24 bytes")
        try:
            return list(struct.unpack("!6f", raw[:24]))
        except struct.error as e:
            self.driver.log_error(f"Struct unpack error: {e}")
            return None

