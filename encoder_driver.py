#!/usr/bin/python3
"""
encoder_driver.py contains the EncoderDriver class

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""

import struct
from hardware.high_level_base_driver import HighLevelBaseReceiver

class EncoderDriver(HighLevelBaseReceiver):
    def receive(self, num_encoders):
        """
        Read the latest raw payload from the BaseDriver buffer,
        unpack into a list of encoder readings as floats.

        Args:
            num_encoders (int): number of encoder values expected

        Returns:
            List[float]: decoded encoder values

        Raises:
            MsgLengthError: if received data is too short
        """
        raw = self.driver.receive()
        expected_length = 4 * num_encoders

        if raw is None:
            return None

        if len(raw) < expected_length:
            raise MsgLengthError(f"Expected {expected_length} bytes, got {len(raw) if raw else 0}.")

        try:
            return list(struct.unpack(f"!{num_encoders}f", raw[:expected_length]))
        except struct.error as e:
            self.driver.log_error(e)
            return None
