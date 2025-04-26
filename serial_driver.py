#!/usr/bin/python3
"""
SerialBaseDriver class for USB and UART communication

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""

import serial
from hardware.base_driver import BaseDriver
import time

class SerialBaseDriver(BaseDriver):
    """Base class for serial communication"""
    SERIALBUFFER = 64 # in bytes
    def __init__(self, msgName, operation, channel, msgID=None, msgIDLength=0, baudrate=115200, timeout=5):
        self.baudrate = baudrate
        self.msgIDLength = msgIDLength
        self.serial_conn = None
        super().__init__(msgName, operation, channel, msgID, timeout)

    def connect(self):
        """Establish a serial connection"""
        try:
            self.serial_conn = serial.Serial(port=self.channel, baudrate=self.baudrate, timeout=self.timeout)
            self.log_connected(self.channel)
            return 0 # for seccuss
        except serial.SerialException as e:
            self.log_warning(f"Failed to connect to {self.channel}: {e}, Retry in 2 seconds")
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            return 1 # for failuer

    def disconnect(self):
        """Close the serial connection"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.stop()

    def clean_buffer(self, opretion):
        if opretion == "send":
                if BaseDriver.channelsOperationsInfo[self.channel]["sentInBuffer"] >= SerialBaseDriver.SERIALBUFFER:
                    self.serial_conn.reset_input_buffer()
                    BaseDriver.channelsOperationsInfo[self.channel]["sentInBuffer"]= 0
        elif opretion == "receive":
                if BaseDriver.channelsOperationsInfo[self.channel]["receivedInBuffer"] >= SerialBaseDriver.SERIALBUFFER:
                    self.serial_conn.reset_output_buffer()
                    BaseDriver.channelsOperationsInfo[self.channel]["receivedInBuffer"] = 0


    @property
    def msgIDLength(self):
        return self.__msgIDLength

    @msgIDLength.setter
    def msgIDLength(self, value):
        if not isinstance(value, int):
            raise TypeError("'msgIDLength' must be of type (int)")
        self.__msgIDLength = value

    @property
    def baudrate(self):
        return self.__baudrate

    @baudrate.setter
    def baudrate(self, value):
        if not isinstance(value, int):
            raise TypeError("'baudrate' must be of type (int)")
        self.__baudrate = value

class SerialSender(SerialBaseDriver):

    def __init__(self, msgName, channel, msgID=None, msgIDLength=0, baudrate=115200, timeout=5):
        super().__init__(msgName, "send", channel, msgID, msgIDLength, baudrate, timeout)

    def threaded_send(self, data):
        if not isinstance(data, bytes):
            raise TypeError("sent data must be of type (bytes)")
        
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    payload = (self.msgID.to_bytes(self.msgIDLength, 'big') + data) if self.msgIDLength else data
                    self.clean_buffer(self.operation)
                    self.serial_conn.write(payload)
                    BaseDriver.channelsOperationsInfo[self.channel]["sentInBuffer"] += len(payload)
                    self.log_sent(data)
                    return 0
                except serial.SerialException as e:
                    self.log_error(f"Error: {e}, Retrying")
                    self.serial_conn.close()
                    self._try_to_connect()
            else:
                self.log_error("Device disconnected, Retrying")
                self._try_to_connect()
        self.log_error(f"Failed to send data: {data} within timeout")
        return 1

    def threaded_receive(self):
        raise NotImplementedError("'SerialSender' object can't be used to receive messages")

    def central_receive(self):
        """Receives all the msgs from channel and adds it to the receivedMsgsBuffer"""
        raise NotImplementedError("'SerialSender' object can't be used to receive messages")

class SerialReceiver(SerialBaseDriver):

    def __init__(self, msgName, channel, msgID=None, msgIDLength=0, baudrate=115200, timeout=5):
        super().__init__(msgName, "receive", channel, msgID, msgIDLength, baudrate, timeout)

    def __handle_received_msg(self, read):
        """handles the msg received by serial including id extraction"""
        if read:
            if self.msgIDLength:
                try:
                    id = int.from_bytes(read[:self.msgIDLength])
                    if id in BaseDriver.receivedMsgsBuffer[self.channel]:
                        msg = read[self.msgIDLength:-1]
                        BaseDriver.receivedMsgsBuffer[self.channel][id] = msg
                        BaseDriver.channelsOperationsInfo[self.channel][self.operation][id] += 1
                        self.log_received(id, msg)
                except Exception as e:
                    self.log_error(e)
            else:
                msg = read[:-1]
                BaseDriver.receivedMsgsBuffer[self.channel][self.msgID] = msg
                BaseDriver.channelsOperationsInfo[self.channel][self.operation][self.msgID] += 1
                self.log_received(self.msgID, msg)
            BaseDriver.channelsOperationsInfo[self.channel]["receivedInBuffer"] += len(read)
            self.clean_buffer(self.operation)

    def __none_all_data(self):
        """
        A function that will be called whenever a problem
        happens to prevent returning old data
        """
        for key in BaseDriver.receivedMsgsBuffer[self.channel].keys():
            BaseDriver.receivedMsgsBuffer[self.channel][key] = None

    def central_receive(self):
        """Receives all the msgs from channel and adds it to the receivedMsgsBuffer"""
        while True:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    read = self.serial_conn.readline()
                    self.__handle_received_msg(read)
                except serial.SerialException as e:
                    self.__none_all_data()
                    self.log_error(f"Error: {e}, Retrying")
                    self.serial_conn.close()
                    self._try_to_connect()
            else:
                self.__none_all_data()
                self.log_error("Device disconnected, Retrying")
                self._try_to_connect()

    def threaded_send(self, msg):
        raise NotImplementedError("'SerialReceiver' object can't be used to send messages")

if __name__ == "__main__":
    pass