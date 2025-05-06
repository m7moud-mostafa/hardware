#!/usr/bin/python3
"""
CANReceiver and CANSender classes to handle hardware communication

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""

import time
import can
from hardware.base_driver import BaseDriver

class CANBaseDriver(BaseDriver):
    """General CAN base driver containing common functionalities"""
    CANBUFFER = 1024  # threshold for buffer stats

    def __init__(
        self,
        msgName,
        operation,
        msgID,
        channel="can0",
        extendedID=False,
        baudrate=250000,
        bustype='socketcan',
        timeout=5
    ):
        # set attributes before BaseDriver init (for connect())
        self.__extendedID = extendedID
        self.__baudrate = baudrate
        self.__bustype = bustype
        super().__init__(msgName, operation, channel, msgID, timeout)
        # spawn the receive thread if needed
        if operation == "receive":
            self._set_central_receiver()


    @property
    def extendedID(self):
        return self.__extendedID

    @property
    def baudrate(self):
        return self.__baudrate

    @property
    def bustype(self):
        return self.__bustype

    def connect(self):
        """Establish CAN bus connection"""
        try:
            self.bus = can.interface.Bus(
                channel=self.channel,
                bustype=self.__bustype,
                baudrate=self.__baudrate
            )
            self.log_connected(self.channel)
            return 0
        except Exception as e:
            self.log_warning(f"Failed to connect CAN bus {self.channel}: {e}")
            return 1

    def disconnect(self):
        """Close the CAN bus connection"""
        try:
            if hasattr(self, 'bus'):
                self.bus.shutdown()
        finally:
            self.stop()

    def clean_buffer(self):
        """Reset buffer counters when thresholds exceeded"""
        pass

class CANSender(CANBaseDriver):
    """CANSender class handles sending messages through CAN"""
    def __init__(self, msgName,
        msgID,
        channel="can0",
        extendedID=False,
        baudrate=250000,
        bustype='socketcan',
        timeout=5
    ):
        super().__init__(
            msgName,
            'send',
            msgID,
            channel,
            extendedID,
            baudrate,
            bustype,
            timeout
        )
        
    def threaded_send(self, data):
        """Send data over CAN with retry, logging, and stats"""
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("CAN data must be bytes or bytearray")

        start = time.time()
        while time.time() - start < self.timeout:
            try:
                msg = can.Message(
                    arbitration_id=self.msgID,
                    data=data,
                    is_extended_id=self.extendedID
                )
                self.bus.send(msg)
                # update stats
                BaseDriver.channelsOperationsInfo[self.channel]['sentInBuffer'] += len(data)
                self._BaseDriver__increment_msg_count()
                self.log_sent(data)
                return 0
            except Exception as e:
                self.log_error(f"CAN send error: {e}, retrying...")
                # attempt reconnect
                try:
                    self.bus.shutdown()
                except:
                    pass
                self._try_to_connect()
        self.log_warning(f"CAN send aborted: timeout for data={data}")
        return 1

    def central_receive(self):
        raise NotImplementedError("'CANSender' object can't be used to receive messages")

class CANReceiver(CANBaseDriver):
    """CANReceiver class handles receiving messages through CAN"""

    def __init__(
        self,
        msgName,
        msgID,
        channel="can0",
        extendedID=False,
        baudrate=250000,
        bustype='socketcan',
        timeout=5,
        recv_timeout=1.0
    ):
        super().__init__(msgName, "receive", msgID, channel,
                         extendedID, baudrate, bustype, timeout)
        self.recv_timeout = recv_timeout

    def __none_all_data(self):
        """Prevent stale data by clearing buffers"""
        for key in BaseDriver.receivedMsgsBuffer[self.channel]:
            BaseDriver.receivedMsgsBuffer[self.channel][key] = None

    def __handle_message(self, msg):
        """Process and buffer incoming CAN message"""
        if msg.arbitration_id == self.msgID:
            payload = bytes(msg.data)
            BaseDriver.receivedMsgsBuffer[self.channel][self.msgID] = payload
            BaseDriver.channelsOperationsInfo[self.channel][self.operation][self.msgID] += 1
            BaseDriver.channelsOperationsInfo[self.channel]['receivedInBuffer'] += len(payload)
            self.clean_buffer()
            self.log_received(self.msgID, payload)

    def central_receive(self):
        """Continuously read CAN messages and buffer them"""
        while getattr(self, '_BaseDriver__isRunning', True):
            try:
                msg = self.bus.recv(timeout=self.recv_timeout)
                if msg is None:
                    continue
                self.__handle_message(msg)
            except Exception as e:
                self.__none_all_data()
                self.log_error(f"CAN receive error: {e}, retrying...")
                try:
                    self.bus.shutdown()
                except:
                    pass
                self._try_to_connect()

    def threaded_send(self, msg):
        raise NotImplementedError("'CANReceiver' object can't be used to send messages")

if __name__ == "__main__":
    pass
