#!/usr/bin/python3
"""
encoder_driver.py contains the EncoderDriver class

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""

import struct
from hardware.can_driver import CANReceiver
from hardware.serial_driver import SerialReceiver
from hardware.base_driver import MsgLengthError

class EncoderBaseDriver:
    """
    Base class for Encoder drivers
    """

    @staticmethod
    def _validate_input(protocol, num_encoders, float_size, endianess):
        """
        Validate the input parameters for the encoder driver.
        :param protocol: Protocol to use ('serial' or 'can')
        :param num_encoders: Number of encoders
        :param float_size: Size of the float (4 for 32-bit, 8 for 64-bit)
        :param endianess: Endianess of the data ('little' or 'big')
        """
        if not isinstance(protocol, str):
            raise TypeError(f"protocol must be a string got {type(protocol)}")
        if protocol not in ['serial', 'can']:
            raise ValueError(f"protocol must be either 'serial' or 'can' got {protocol}")

        # User input validation
        if not isinstance(float_size, int):
            raise TypeError(f"float_size must be an integer got {type(float_size)}")
        if float_size not in [4, 8]:
            raise ValueError(f"float_size must be either 4 or 8 got {float_size}")

        if not isinstance(endianess, str):
            raise TypeError(f"endianess must be a string got {type(endianess)}")
        if endianess not in ['little', 'big']:
            raise ValueError(f"endianess must be either 'little' or 'big' got {endianess}")

        if not isinstance(num_encoders, int):
            raise TypeError(f"num_encoders must be an integer got {type(num_encoders)}")
        if num_encoders < 1:
            raise ValueError("num_encoders must be greater than 0")
        if protocol == 'can':
            if num_encoders * float_size > 8:
                raise ValueError(f"num_encoders * float_size must be less than or equal to 8 got {num_encoders * float_size}")

    @staticmethod
    def _unpack_data(raw, num_encoders, float_size, endianess):
        """
        Unpack the raw data received from the encoder.
        :param raw: Raw data received
        :param num_encoders: Number of encoders
        :param float_size: Size of the float (4 for 32-bit, 8 for 64-bit)
        :param endianess: Endianess of the data ('little' or 'big')
        :return: Unpacked data
        """
        fmt_char = 'f' if float_size == 4 else 'd'
        prefix = '<' if endianess == 'little' else '>'
        expected_length = float_size * num_encoders

        unpacked = None
        if raw :
            if len(raw) != expected_length:
                raise MsgLengthError(f"Expected {expected_length} bytes, got {len(raw) if raw else 0}.")

            unpacked = struct.unpack(prefix + fmt_char * num_encoders, raw)
            if num_encoders == 1:
                return unpacked[0]
            else:
                return tuple(unpacked)
        else:
            return unpacked

class EncoderCANDriver(CANReceiver, EncoderBaseDriver):
    """
    Encoder driver to handle Encoder data reception over CAN bus
    """
    def receive(self, num_encoders: int = 1, float_size: int = 8, endianess: str = 'little'):
        """
        Receive data from the Encoder over CAN bus.
        :param float_size: Size of the float (4 for 32-bit, 8 for 64-bit)
        :param endianess: Endianess of the data ('little' or 'big')
        :param num_encoders: Number of encoders to read
        :return: List of encoder values
        """
        self._validate_input('can', num_encoders, float_size, endianess)
        raw = super().receive()

        try:
            unpacked = self._unpack_data(raw, num_encoders, float_size, endianess)
            return unpacked
        except (struct.error, MsgLengthError) as e:
            self.log_error(f"Error unpacking Encoders data: {e}")
            return None

class EncoderSerialDriver(SerialReceiver, EncoderBaseDriver):
    """
    Encoder driver to handle Encoder data reception over Serial
    """
    def receive(self, num_encoders: int = 1, float_size: int = 8, endianess: str = 'little'):
        """
        Receive data from the Encoder over Serial.
        :param float_size: Size of the float (4 for 32-bit, 8 for 64-bit)
        :param endianess: Endianess of the data ('little' or 'big')
        :param num_encoders: Number of encoders to read
        :return: List of encoder values
        1. If num_encoders is 1, return a single value.
        2. If num_encoders is greater than 1, return a tuple of values.
        """
        self._validate_input('serial', num_encoders, float_size, endianess)
        raw = super().receive()

        try:
            unpacked = self._unpack_data(raw, num_encoders, float_size, endianess)
            return unpacked
        except (struct.error, MsgLengthError) as e:
            self.log_error(f"Error unpacking Encoders data: {e}")
            return None

if __name__ == "__main__":
    import time
    # Create an instance of EncoderSerialDriver
    encoder_driver = EncoderSerialDriver(
        msgName="EncoderData",
        channel="/dev/ttyACM0",
        msgID=0x12,
        msgIDLength=1,
        baudrate=115200,
        timeout=5
    )

    print("Starting serial communication test...")
    while True:
        # Receive data for two encoders, each as a 4-byte float in little-endian format
        data = encoder_driver.receive(num_encoders=2, float_size=4, endianess='little')
        if data is not None:
            print(f"Received encoder data: {data}")
        else:
            print("Failed to receive data")
        time.sleep(0.01)  # Adjust sleep time as needed