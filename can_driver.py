#!/usr/bin/python3
"""
CANReceiver and CANSender classes to handle hardware communication

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""

import can
from hardware.base_driver import BaseDriver

class CANBaseDriver(BaseDriver):
    """General CAN base driver containing common functionalities"""

    def __init__(self, msgName, operation, msgID, extendedID=False, channel="can0", bitrate=250000, bustype='socketcan'):
        super().__init__(msgName, operation, msgID)
        self.channel = channel
        self.extendedID = extendedID
        self.bitrate = bitrate
        self.bustype = bustype

    @property
    def bustype(self):
        """Returns the bustype value"""
        return self.__bustype

    @bustype.setter
    def bustype(self, value):
        """Sets the bustype value"""
        if not isinstance(value, str):
            raise TypeError("'bustype' value must be of type (str)")
        self.__bustype = value

    @property
    def bitrate(self):
        """Returns the bitrate value"""
        return self.__bitrate

    @bitrate.setter
    def bitrate(self, value):
        """Sets the bitrate value"""
        if not isinstance(value, int):
            raise TypeError("'bitrate' value must be of type (int)")
        if value <= 0:
            raise ValueError("'bitrate' must have a positive value")
        self.__bitrate = value

    @property
    def channel(self):
        """Returns the channel value"""
        return self.__channel

    @channel.setter
    def channel(self, value):
        """Sets the channel name value"""
        if not isinstance(value, str):
            raise TypeError("'channel' value must be of type (str)")
        self.__channel = value

    @property
    def extendedID(self):
        """Returns the extendedID value"""
        return self.__extendedID

    @extendedID.setter
    def extendedID(self, value):
        """Sets the extendedID value"""
        if not isinstance(value, bool):
            raise TypeError("extendedID value must be of type (bool)")
        self.__extendedID = value

class CANSender(CANBaseDriver):
    """CANSender class handles sending messages through CAN"""

    def __init__(self, msgName, msgID, extendedID=False, channel="can0", bitrate=250000, bustype='socketcan'):
        super().__init__(msgName, "send", msgID, extendedID, channel, bitrate, bustype)
        self.bus = can.interface.Bus(channel=self.__channel, bustype=self.__bustype, bitrate=self.__bitrate)

    def send(self, data):
        """Send a CAN message"""
        try:
            msg = can.Message(arbitration_id=self.__msgID, data=data, is_extended_id=self.__extendedID)
            self.bus.send(msg)
            print(f"Sent CAN message: ID={self.__msgID}, Data={data}")
        except can.CanError as e:
            print(f"Failed to send CAN message: {e}")

    def receive(self):
        raise NotImplementedError("'CANSender' object can't be used to receive messages")

class CANReceiver(CANBaseDriver):
    """CANReceiver class handles receiving messages through CAN"""

    def __init__(self, msgName, msgID, extendedID=False, channel="can0", bitrate=250000, bustype='socketcan'):
        super().__init__(msgName, "receive", msgID, extendedID, channel, bitrate, bustype)
        self.__filter = [{
            "can_id": self.__msgID, 
            "can_mask": 0x7FF if not self.__extendedID else 0x1FFFFFFF, 
            "extended": self.__extendedID
        }]
        self.bus = can.interface.Bus(channel=self.__channel, bustype=self.__bustype, bitrate=self.__bitrate, can_filters=self.__filter)

    def receive(self):
        """Receive a CAN message"""
        msg = self.bus.recv(timeout=5.0)  # will wait 5 seconds for the messages before returning None
        if msg:
            print(f"Received CAN message: ID={msg.__arbitration_id}, Data={msg.data}")
            return msg
        else:
            print("No CAN message received within timeout.")
            return None

    def send(self):
        raise NotImplementedError("'CANReceiver' object can't be used to send messages")
