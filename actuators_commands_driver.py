#!/usr/bin/python3
"""
actuator_commands_driver.py contains the actuator_commands class

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""
import struct
from hardware.base_driver import BaseDriver, MsgLengthError
from hardware.can_driver import CANSender

class ActuatorsCommandsDriver:
    """
    This class is responsible for sending actuator commands to the low-level driver.
    """
    def __init__(self, driver, acutators_commands_struct: str, actuators_names: list = None, endianess: str = "little"):
        """
        Initializes the ActuatorsCommandsDriver with a low-level driver and actuator commands structure.

        :param driver: The low-level driver to send commands to.
        :param acutators_commands_struct: The structure of the actuator commands message.
        """
        self.driver = driver
        self.acutators_commands_struct = acutators_commands_struct
        self.actuators_names = actuators_names
        self.endianess = endianess

    @property
    def endianess(self):
        """Returns the endianess of the actuator commands structure."""
        return self._endianess
    @endianess.setter
    def endianess(self, endianess):
        """Sets the endianess of the actuator commands structure."""
        if endianess not in ["little", "big"]:
            raise ValueError(f"endianess must be 'little' or 'big', got {endianess}")
        prefix = "<" if endianess == "little" else ">"
        self._endianess = prefix

    @property
    def actuators_names(self):
        """Returns the actuator names."""
        return self._actuators_names

    @actuators_names.setter
    def actuators_names(self, names):
        """Sets the actuator names."""
        if not isinstance(names, list):
            raise TypeError(f"actuators_names must be a list, got {type(names).__name__}")
        if not all(isinstance(name, str) for name in names):
            raise TypeError(f"actuators_names must be a list of strings, got {type(names).__name__}")
        if len(names) != len(set(names)):
            raise ValueError(f"actuators_names must contain unique names, got {names}")
        if len(names) != len(self.acutators_commands_struct):
            raise ValueError(
                f"actuators_names length must match acutators_commands_struct length, "
                f"got {len(names)} and {len(self.acutators_commands_struct)}"
            )
        self._actuators_names = names

    @property
    def driver(self):
        """Returns the low-level driver."""
        return self._driver

    @driver.setter
    def driver(self, driver):
        """Sets the low-level driver."""
        if not isinstance(driver, BaseDriver):
            raise TypeError(
                f"driver must be an instance of BaseDriver or a subclass of BaseDriver, got {type(driver).__name__}"
            )
        if "Sender" not in driver.__class__.__name__:
            raise TypeError(
                f"driver must be a Sender class, got {driver.__class__.__name__}"
            )
        if not hasattr(driver, "send"):
            raise AttributeError(
                f"driver must have a send method, got {driver.__class__.__name__}"
            )
        self._driver = driver

    @property
    def acutators_commands_struct(self):
        """Returns the actuator commands structure."""
        return self._acutators_commands_struct

    @acutators_commands_struct.setter
    def acutators_commands_struct(self, struct_string):
        """
        Sets the actuator commands structure.
        :param struct_string: The structure of the actuator commands message.
        b - int8_t, B - uint8_t
        h - int16_t, H - uint16_t
        i - int32_t, I - uint32_t
        q - int64_t, Q - uint64_t
        e - float16_t
        f - float32_t
        d - float64_t
        ? - bool
        """
        TYPE_SIZES = {
        'b': 1, 'B': 1,
        '?': 1,
        'h': 2, 'H': 2,
        'i': 4, 'I': 4,
        'q': 8, 'Q': 8,
        'e': 2,
        'f': 4,
        'd': 8,
        }
        if not isinstance(struct_string, str):
            raise TypeError(f"acutators_commands_struct must be a string, got {type(struct_string).__name__}")
        if not all(char in TYPE_SIZES for char in struct_string):
                raise ValueError(
                    f"acutators_commands_struct contains invalid characters. "
                    f"Allowed types are: {', '.join(TYPE_SIZES.keys())}"
                )
        msg_len = sum(TYPE_SIZES[char] for char in struct_string)
        if isinstance(self.driver, CANSender):
            if msg_len > 8:
                raise MsgLengthError(
                    f"acutators_commands_struct length exceeds 8 bytes: {msg_len} bytes"
                )
        self._acutators_commands_struct = struct_string

    def send(self, *args):
        """
        Sends the actuator commands to the low-level driver.
        :param args: The actuator commands to send.
        """
        if len(args) != len(self.acutators_commands_struct):
            raise ValueError(
                f"Number of arguments must match acutators_commands_struct length, "
                f"got {len(args)} and {len(self.acutators_commands_struct)}"
            )
        for i, arg in enumerate(args):
            if not isinstance(arg, (int, float, bool)):
                raise TypeError(
                    f"Argument {i}-{self.actuators_names[i]} must be an int, float or bool, got {type(arg).__name__}"
                )
        packed_data = struct.pack(self.endianess + self.acutators_commands_struct, *args)
        status = self.driver.send(packed_data)
        return status

if __name__ == "__main__":
    from hardware.serial_driver import SerialSender
    import time
    # Example usage
    # Create a SerialSender instance
    msgName = "actuator_commands"
    channel = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_854353331313517061C2-if00"
    driver =  SerialSender(msgName, channel, msgID=0x10, msgIDLength=1, baudrate=115200, timeout=5)

    # Define the actuator commands structure and names
    acutators_commands_struct = "bf"
    actuators_names = ["actuator1", "actuator2"]

    # Create an ActuatorsCommandsDriver instance
    actuator_driver = ActuatorsCommandsDriver(driver, acutators_commands_struct, actuators_names)

    # Send actuator commands
    while True:
        # Example values for actuator commands
        actuator1_value = 1
        actuator2_value = 2.5
        # Send the commands
        status = actuator_driver.send(actuator1_value, actuator2_value)
        if status == 0:
            print("Commands sent successfully")
        else:
            print("Failed to send commands")
        # Sleep for a while before sending the next commands
        time.sleep(0.5)
