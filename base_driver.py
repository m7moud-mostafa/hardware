#!/usr/bin/python3
"""
BaseDriver class to handle hardware communication with logging.

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""

from abc import ABC, abstractmethod
from hardware.logging_mixin import LoggingMixin
import threading
import time

class BaseDriver(LoggingMixin, ABC):
    """
    BaseDriver class with logging capabilities inherited from LoggingMixin.
    Includes necessary functions for any driver.
    """
    instancesInfo = {}
    receivedMsgsBuffer = {}
    channelsOperationsInfo = {}
    def __init__(self, msgName, operation, channel, msgID, timeout=5):
        """Initialize the driver and log its creation."""
        # Set attributes
        self.msgName = msgName
        self.operation = operation
        self.channel = channel
        self.msgID = msgID
        self.timeout = timeout
        self.__numOfMsgs = 0
        self.__isRunning = True
        self._isConnected = False
        self.__pending_message = None
        self.central_receive_thread = None

        # Call the parent class's __init__ (LoggingMixin) to initialize the logger
        super().__init__()
        self._try_to_connect()
        self.__store_info()
        self._set_central_receiver()


        self.log_instance_created()

    def __store_info(self):
        """Stores info of instances when createtion"""

        BaseDriver.instancesInfo[self.msgName] = {
            "id": self.msgID,
            "protocol": self.__class__.__name__,
            "channel": self.channel,
            "operation": self.operation,
            "running": self.__isRunning,
            "numOfMsgs": self.__numOfMsgs
        }

        if not (self.channel in BaseDriver.channelsOperationsInfo):
            BaseDriver.channelsOperationsInfo[self.channel] = {"receive": {}, "send": {}, "receivedInBuffer": 0, "sentInBuffer": 0}

        BaseDriver.channelsOperationsInfo[self.channel][self.operation][self.msgID] = 0

    def _set_central_receiver(self):
        """sets up central receiver variable"""
        if self.operation == "receive":
            if not (self.channel in BaseDriver.receivedMsgsBuffer):
                BaseDriver.receivedMsgsBuffer[self.channel] = {}
                BaseDriver.receivedMsgsBuffer[self.channel][self.msgID] = None
                try:
                    self.central_receive_thread = threading.Thread(target=self.central_receive)
                    self.central_receive_thread.start()
                except Exception as e:
                    self.log_error(e)
            BaseDriver.receivedMsgsBuffer[self.channel][self.msgID] = None


    @abstractmethod
    def central_receive(self):
        """Receives all the msgs from channel and adds it to the receivedMsgsBuffer"""
        pass

    def _try_to_connect(self):
        """Keep trying to connect until successful, with a maximum retry count."""
        max_retries = 60 * 3 / 2 
        retries = 0
        while retries < max_retries:
            status = self.connect()
            if not status:  # 0 indicates success
                self._isConnected = True
                return
            else:
                self._isConnected = False
                retries += 1
                time.sleep(2)
        self.log_error("Max connection attempts reached.")
        raise ConnectionError("Unable to establish connection after maximum retries.")


    def __increment_msg_count(self):
        """A function used to increase the self.__numOfMsgs"""
        if self.operation == "send":
            BaseDriver.channelsOperationsInfo[self.channel][self.operation][self.msgID] += 1
            self.__numOfMsgs += 1
            BaseDriver.instancesInfo[self.msgName]["numOfMsgs"] = self.__numOfMsgs
        else:
            self.__numOfMsgs = BaseDriver.channelsOperationsInfo[self.channel][self.operation][self.msgID]
            BaseDriver.instancesInfo[self.msgName]["numOfMsgs"] = self.__numOfMsgs


    def send(self, msg):
        """A function that sends the message in a thread"""
        statusContainer = []
        if self.__pending_message is None:
            self.__pending_message = msg # to prevent from dublicate messages
            
            try:
                th = threading.Thread(target=lambda: statusContainer.append(self.threaded_send(msg)))
                th.start()
                th.join()
                if not statusContainer[0]:
                   self.__increment_msg_count()
                return statusContainer[0]
            except Exception as e:
                self.log_error(e)
                return 1 # failure
            finally:
                self.__pending_message = None

    def receive(self):
        """A function that receive the message in a thread"""
        msg = BaseDriver.receivedMsgsBuffer[self.channel][self.msgID]
        self.__increment_msg_count()
        # self.log_received(msg)
        return msg


    def stop(self):
        """Stops the driver safely and logs the event."""
        self.__isRunning = False
        BaseDriver.instancesInfo[self.__msgName]["running"] = self.__isRunning
        self.log_stop()

    @abstractmethod
    def connect(self):
        """To be implemented in child class"""
        pass

    @abstractmethod
    def disconnect(self):
        """To be implemented in child class"""
        pass

    @abstractmethod
    def threaded_send(self, msg):
        """To be implemented in child class"""
        pass

    # @abstractmethod
    # def threaded_receive(self):
    #     """To be implemented in child class"""
    #     pass

    def __del__(self):
        """Ensure the serial connection is closed on deletion"""
        self.disconnect()

################### Getters and Setters ###################
    @property
    def msgName(self):
        """Returns the msg name"""
        return self.__msgName

    @msgName.setter
    def msgName(self, value):
        """Sets the msg name value"""
        if not isinstance(value, str):
            raise TypeError("'msgName' must be of type (str)")
        if value in BaseDriver.instancesInfo:
            raise ValueError("msgName must have a unique value")
        self.__msgName = value

    @property
    def operation(self):
        """Returns the operation type"""
        return self.__operation

    @operation.setter
    def operation(self, value):
        """Sets the operation type value"""
        if not isinstance(value, str):
            raise TypeError("operation must be of type (str)")
        if value not in ["send", "receive"]:
            raise ValueError("operation must be either 'send' or 'receive'")
        self.__operation = value

    @property
    def msgID(self):
        """Returns the msgID value"""
        return self.__msgID

    @msgID.setter
    def msgID(self, value):
        """Sets the msgID type value with uniqueness and None checks per operation and channel"""
        if value is not None and not isinstance(value, int):
            raise TypeError("msgID must be an integer or None")

        existing = BaseDriver.instancesInfo.values() if BaseDriver.instancesInfo else []
        same_op_chan = [info for info in existing
                        if info["operation"] == self.operation and info["channel"] == self.channel]

        if value is None:
            if same_op_chan:
                raise ValueError(
                    f"Cannot set msgID to None: another instance in operation '{self.operation}' "
                    f"and channel '{self.channel}' already has msgID or msgID=None"
                )
        else:
            if any(info["id"] is None for info in same_op_chan):
                raise ValueError(
                    f"Cannot set msgID to {value}: an instance in operation '{self.operation}' "
                    f"and channel '{self.channel}' has msgID=None"
                )
            if any(info["id"] == value for info in same_op_chan):
                raise ValueError(
                    f"An instance with msgID {value} already exists in operation '{self.operation}' "
                    f"and channel '{self.channel}'"
                )
        self.__msgID = value

    @property
    def timeout(self):
        """Returns the timout"""
        return self.__timeout

    @timeout.setter
    def timeout(self, value):
        """Sets the timeout value"""
        if not isinstance(value, int):
            raise TypeError("'timeout' must be of type (int)")
        self.__timeout = value

    @property
    def numOfMsgs(self):
        """Returns the numOfMsgs, It got not setter"""
        return self.__numOfMsgs

    @property
    def channel(self):
        return self.__channel

    @channel.setter
    def channel(self, value):
        if not isinstance(value, str):
            raise TypeError("'channel' must be of type (str)")
        self.__channel = value
