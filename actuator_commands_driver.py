#!/usr/bin/python3
"""
actuator_commands_driver.py contains the actuator_commands class

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""
import struct
from hardware.high_level_base_driver import HighLevelBaseSender

class ActuatorCommandsDriver(HighLevelBaseSender):
    def send(self, cmd1, cmd2):
        """Sends the actuator_commands msgs and converts binary data into floats"""
        cmd1 = max(-100, min(100, int(cmd1)))
        cmd2 = max(-100, min(100, int(cmd2)))

        # Pack as two signed 8-bit integers
        msg = struct.pack("bb", cmd1, cmd2)

        # Send via low-level driver
        self.driver.send(msg)
