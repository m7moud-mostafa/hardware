#!/usr/bin/python3
"""
SPIBaseDriver class for SPI communication

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""

import time
import spidev
import threading
from hardware.base_driver import BaseDriver

class SPIBaseDriver(BaseDriver):
    """Base class for SPI communication with buffer management and retries"""
    SPIBUFFER = 4096  # buffer threshold in bytes

    def __init__(self, msgName, operation, bus, device,
                 msgID=None, msgIDLength=0, msgLenLength=0,
                 mode=0, max_speed_hz=500000, timeout=5):
        self.bus = bus
        self.device = device
        self.mode = mode
        self.max_speed_hz = max_speed_hz
        self.msgIDLength = msgIDLength
        self.msgLenLength = msgLenLength
        self.spi = None
        super().__init__(msgName, operation, f"{bus}.{device}", msgID, timeout)
        if operation == "receive":
            # Threaded receiver
            self._set_central_receiver()

    def connect(self):
        """Establish SPI connection"""
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(self.bus, self.device)
            self.spi.mode = self.mode
            self.spi.max_speed_hz = self.max_speed_hz
            self.log_connected(f"bus={self.bus}, device={self.device}")
            return 0
        except Exception as e:
            self.log_warning(f"Failed to open SPI bus={self.bus}, device={self.device}: {e}")
            if self.spi:
                self.spi.close()
            return 1

    def disconnect(self):
        """Close the SPI connection"""
        if self.spi:
            self.spi.close()
            self.stop()

    @property
    def msgLenLength(self):
        return self.__msgLenLength

    @msgLenLength.setter
    def msgLenLength(self, value):
        if not isinstance(value, int):
            raise TypeError("'msgLenLength' must be of type (int)")
        self.__msgLenLength = value

    def clean_buffer(self):
        """Reset buffer counters if thresholds exceeded"""
        info = BaseDriver.channelsOperationsInfo[self.channel]
        if info["sentInBuffer"] >= SPIBaseDriver.SPIBUFFER:
            info["sentInBuffer"] = 0
            self.log_info("SPI TX buffer counter reset")
        if info["receivedInBuffer"] >= SPIBaseDriver.SPIBUFFER:
            info["receivedInBuffer"] = 0
            self.log_info("SPI RX buffer counter reset")

class SPISender(SPIBaseDriver):

    def __init__(self, msgName, bus, device,
                 msgID=None, msgIDLength=0, msgLenLength=0,
                 mode=0, max_speed_hz=500000, timeout=5):
        super().__init__(msgName, "send", bus, device,
                         msgID, msgIDLength, msgLenLength,
                         mode, max_speed_hz, timeout)

    def threaded_send(self, data):
        """Send data over SPI with ID, length headers, retry & buffer cleanup"""
        if not isinstance(data, bytes):
            raise TypeError("sent data must be of type (bytes)")

        # Build header + payload
        payload = b''
        if self.msgLenLength:
            payload += len(data).to_bytes(self.msgLenLength, 'big')
        if self.msgIDLength:
            payload += self.msgID.to_bytes(self.msgIDLength, 'big')
        payload += data

        start = time.time()
        while time.time() - start < self.timeout:
            try:
                self.clean_buffer()
                self.spi.xfer2(list(payload))
                # Update counters
                BaseDriver.channelsOperationsInfo[self.channel]["sentInBuffer"] += len(payload)
                self.__increment_msg_count()
                self.log_sent(data)
                return 0
            except Exception as e:
                self.log_error(f"SPI send error: {e}, retrying...")
                self.spi.close()
                self._try_to_connect()
        self.log_warning(f"SPI send aborted: timeout exceeded for data={data}")
        return 1

    def central_receive(self):
        raise NotImplementedError("'SPISender' object can't be used to receive messages")

class SPIReceiver(SPIBaseDriver):

    def __init__(self, msgName, bus, device,
                 msgID=None, msgIDLength=0, msgLenLength=0,
                 mode=0, max_speed_hz=500000, timeout=5,
                 packet_size=256):
        self.packet_size = packet_size
        super().__init__(msgName, "receive", bus, device,
                         msgID, msgIDLength, msgLenLength,
                         mode, max_speed_hz, timeout)

    def __none_all_data(self):
        """Prevent stale data: clear buffers on error/disconnect"""
        for key in BaseDriver.receivedMsgsBuffer[self.channel]:
            BaseDriver.receivedMsgsBuffer[self.channel][key] = None

    def __handle_received_msg(self, raw):
        """Handle incoming packet, extract ID & payload"""
        if not raw:
            return
        data = bytes(raw)
        # Strip length header
        if self.msgLenLength:
            data = data[self.msgLenLength:]
        # ID + payload
        if self.msgIDLength:
            msg_id = int.from_bytes(data[:self.msgIDLength], 'big')
            payload = data[self.msgIDLength:]
        else:
            msg_id = self.msgID
            payload = data
        # Store if valid
        if msg_id in BaseDriver.receivedMsgsBuffer[self.channel]:
            BaseDriver.receivedMsgsBuffer[self.channel][msg_id] = payload
            BaseDriver.channelsOperationsInfo[self.channel][self.operation][msg_id] += 1
            BaseDriver.channelsOperationsInfo[self.channel]["receivedInBuffer"] += len(raw)
            self.log_received(msg_id, payload)
        # Cleanup if needed
        self.clean_buffer()

    def central_receive(self):
        """Continuously read variable-length or fixed packets"""
        while True:
            if not self._isConnected:
                self.__none_all_data()
                self.log_error("SPI disconnected, retrying...")
                self._try_to_connect()
                continue
            try:
                if self.msgLenLength:
                    # Read length header
                    header = self.spi.xfer2([0x00] * self.msgLenLength)
                    length = int.from_bytes(bytes(header), 'big')
                    # Read rest of packet
                    raw = self.spi.xfer2([0x00] * (self.msgIDLength + length))
                    full = header + bytes(raw)
                else:
                    full = bytes(self.spi.xfer2([0x00] * self.packet_size))
                self.__handle_received_msg(full)
            except Exception as e:
                self.__none_all_data()
                self.log_error(f"SPI receive error: {e}, retrying...")
                if self.spi:
                    self.spi.close()
                self._try_to_connect()

    def threaded_send(self, msg):
        raise NotImplementedError("'SPIReceiver' object can't be used to send messages")

if __name__ == "__main__":
    pass
