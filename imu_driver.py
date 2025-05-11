#!/usr/bin/python3
"""
imu_driver.py contains the IMUDriver class

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""

import struct
from hardware.can_driver import CANReceiver
from hardware.serial_driver import SerialReceiver

class IMUCANDriver:
    """
    IMU driver to handle IMU data reception over CAN bus
    """
    def __init__(
        self,
        msgName: str,
        msgID: list[int],
        channel="can0",
        extendedID=False,
        baudrate=500000,
        bustype='socketcan',
        timeout=5,
        recv_timeout=1.0
    ):
        self.msgName = msgName
        self.msgID = msgID

        self.msgNames = [f'{msgName}_ax',
                    f'{msgName}_ay',
                    f'{msgName}_az',
                    f'{msgName}_gx',
                    f'{msgName}_gy',
                    f'{msgName}_gz']
        self.msgIDs = [msgID[0], msgID[1], msgID[2], msgID[3], msgID[4], msgID[5]]

        self.drivers = []
        for i in range(6):
            driver = CANReceiver(
                msgName=self.msgNames[i],
                msgID=[self.msgIDs[i]],
                channel=channel,
                extendedID=extendedID,
                baudrate=baudrate,
                bustype=bustype,
                timeout=timeout,
                recv_timeout=recv_timeout
            )
            self.drivers.append(driver)

    @property
    def msgID(self):
        return self._msgID

    @msgID.setter
    def msgID(self, value):
        if not hasattr(value, '__iter__') or not all(isinstance(i, int) for i in value):
            raise ValueError("msgID must be an iterable containing integers")
        if len(value) != 6:
            raise ValueError("msgID must contain exactly 6 integers")
        self._msgID = list(value)

    def receive(self, float_size: int = 8, endianess: str = 'little'):
        """
        Receive data from the IMU
        """
        # User input validation
        if not isinstance(float_size, int):
            raise ValueError("float_size must be an integer")
        if float_size not in [4, 8]:
            raise ValueError("float_size must be either 4 or 8")

        if not isinstance(endianess, str):
            raise ValueError("endianess must be a string")
        if endianess not in ['little', 'big']:
            raise ValueError("endianess must be either 'little' or 'big'")

        # Build struct format
        fmt_char = 'f' if float_size == 4 else 'd'
        prefix = '<' if endianess == 'little' else '>'

        # Receive raw data
        data = []
        for driver in self.drivers:
            raw = driver.receive()
            if raw is not None and len(raw) != float_size:
                raise ValueError(
                    f"Received data for '{driver.msgName}' is {len(raw)} bytes, "
                    f"expected {float_size}"
                )
            data.append(raw)

        # Unpack
        unpacked = []
        try:
            for raw in data:
                if raw is None:
                    unpacked.append(None)
                else:
                    val = struct.unpack(prefix + fmt_char, raw)[0]
                    unpacked.append(val)
        except struct.error as e:
            raise ValueError(f"Error unpacking IMU data: {e}")

        return tuple(unpacked)

class IMUSerialDriver(SerialReceiver):
    """
    IMU driver to handle IMU data reception over serial
    """

    def receive(self, float_size: int = 4, endianess: str = 'little'):
        """
        Receive data from the IMU
        """
        # User input validation
        if not isinstance(float_size, int):
            raise ValueError("float_size must be an integer")
        if float_size not in [4, 8]:
            raise ValueError("float_size must be either 4 or 8")

        if not isinstance(endianess, str):
            raise ValueError("endianess must be a string")
        if endianess not in ['little', 'big']:
            raise ValueError("endianess must be either 'little' or 'big'")

        total_data_length = float_size * 6

        # Build struct format
        fmt_char = 'f' if float_size == 4 else 'd'
        prefix = '<' if endianess == 'little' else '>'

        # Receive raw data
        raw = super().receive()
        if raw and len(raw) != total_data_length:
            raise ValueError(
                f"Received data for '{self.msgName}' is {len(raw)} bytes, "
                f"expected {total_data_length}"
            )

        # Unpack
        unpacked = []
        try:
            unpacked = struct.unpack(prefix + fmt_char * 6, raw)
        except struct.error as e:
            raise ValueError(f"Error unpacking IMU data: {e}")

        return tuple(unpacked)
