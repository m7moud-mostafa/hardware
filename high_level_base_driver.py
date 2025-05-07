#!/usr/bin/python3
"""
high_level_base_driver.py contains the base class

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""
from hardware.serial_driver import SerialReceiver
from hardware.can_driver import CANReceiver


class HighLevelBaseReceiver:
    def __init__(
        self,
        protocol,
        msgName,
        msgID,
        channel,
        msgIDLength,
        extendedID=False,
        baudrate=250000,
        bustype='socketcan',
        timeout=5,
        recv_timeout=1.0
    ):
        self.protocol = protocol.lower()

        if self.protocol == "serial":
            self.driver = SerialReceiver(msgName, channel, msgID, msgIDLength, baudrate, timeout)
        elif self.protocol == "can":
            self.driver = CANReceiver(
                msgName=msgName,
                msgID=msgID,
                channel=channel,
                extendedID=extendedID,
                baudrate=baudrate,
                bustype=bustype,
                timeout=timeout,
                recv_timeout=recv_timeout
            )
        else:
            raise ValueError("Unsupported protocol: must be 'serial' or 'can'")

class HighLevelBaseSender:
    def __init__(
        self,
        msgName,
        msgID,
        channel,
        msgIDLength,
        extendedID=False,
        baudrate=250000,
        bustype='socketcan',
        timeout=5
    ):
        self.protocol = protocol.lower()

        if self.protocol == "serial":
            self.driver = SerialReceiver(msgName, channel, msgID, msgIDLength, baudrate, timeout)
        elif self.protocol == "can":
            self.driver = CANReceiver(
                msgName=msgName,
                msgID=msgID,
                channel=channel,
                extendedID=extendedID,
                baudrate=baudrate,
                bustype=bustype,
                timeout=timeout,
            )
        else:
            raise ValueError("Unsupported protocol: must be 'serial' or 'can'")
