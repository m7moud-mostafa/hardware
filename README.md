# Hardware Drivers Python Library

This document provides comprehensive documentation for the hardware drivers python library, supporting Serial, SPI, CAN, Encoder, IMU, and Actuator Commands drivers. It covers initialization, configuration, usage, and shutdown for all supported buses and device types.

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [BaseDriver Highlights](#basedriver-highlights)
4. [Serial Drivers](#serial-drivers)
5. [SPI Drivers](#spi-drivers)
6. [CAN Drivers](#can-drivers)
7. [Encoder Drivers](#encoder-drivers)
8. [IMU Drivers](#imu-drivers)
9. [Actuators Commands Driver](#actuators-commands-driver)
10. [Configuration Options](#configuration-options)
11. [Usage Examples](#usage-examples)
12. [Logging & Debugging](#logging--debugging)
13. [Shutdown & Cleanup](#shutdown--cleanup)

---

## Overview

The hardware package provides robust, thread-safe drivers for:

- **Serial (USB/UART)**
- **SPI**
- **CAN**
- **Encoders** (Serial & CAN)
- **IMU** (Serial & CAN)
- **Actuator Commands** (Serial & CAN)

All drivers inherit from a common [`BaseDriver`](base_driver.py), providing:

- Automatic connection retries
- Threaded receive loops
- Message-ID framing
- Buffer-overflow detection & cleanup
- Centralized send/receive counters
- Logging of events, errors, and statistics

---

## Installation

1. Ensure dependencies are installed:
   ```bash
   pip install pyserial spidev python-can
   ```
2. Place the `hardware` package in your project PYTHONPATH.

---

## BaseDriver Highlights

All drivers extend [`hardware.base_driver.BaseDriver`](base_driver.py), which provides:

- `send(data: bytes) -> int`
- `receive() -> bytes`
- Automatic retry in `_try_to_connect()`
- `stop()` for graceful shutdown
- Class attributes:
  - `instancesInfo` (per-driver metadata)
  - `channelsOperationsInfo` (counters & buffer stats)
  - `receivedMsgsBuffer` (shared receive buffers)

---

## Serial Drivers

### [`SerialSender`](serial_driver.py)

```python
from hardware.serial_driver import SerialSender

sender = SerialSender(
    msgName='telemetry',
    channel='/dev/ttyUSB0',
    msgID=0x10,
    msgIDLength=1,
    baudrate=115200,
    timeout=5,
)
status = sender.send(b'hello world')  # 0 on success, 1 on failure
```

### [`SerialReceiver`](serial_driver.py)

```python
from hardware.serial_driver import SerialReceiver

receiver = SerialReceiver(
    msgName='telemetry',
    channel='/dev/ttyUSB0',
    msgID=0x10,
    msgIDLength=1,
    baudrate=115200,
    timeout=5,
)
# In background thread:
data = receiver.receive()  # Latest bytes or None
```

---

## SPI Drivers

### [`SPISender`](spi_driver.py)

```python
from hardware.spi_driver import SPISender

sender = SPISender(
    msgName='config',
    bus=0,
    device=1,
    msgID=0x01,
    msgIDLength=1,
    msgLenLength=2,
    mode=0,
    max_speed_hz=1_000_000,
    timeout=3,
)
status = sender.send(b'CONFIG_DATA')  # 0 on success
```

### [`SPIReceiver`](spi_driver.py)

```python
from hardware.spi_driver import SPIReceiver

receiver = SPIReceiver(
    msgName='config',
    bus=0,
    device=1,
    msgID=0x01,
    msgIDLength=1,
    msgLenLength=2,
    timeout=3,
    packet_size=512,
)
# Internal thread buffers data
payload = receiver.receive()  # Latest payload or None
```

---

## CAN Drivers

### [`CANSender`](can_driver.py)

```python
from hardware.can_driver import CANSender

sender = CANSender(
    msgName='engine_ctrl',
    msgID=0x100,
    extendedID=False,
    channel='can0',
    bitrate=500000,
    bustype='socketcan',
    timeout=5,
)
status = sender.send(b'\x01\x02\x03')  # 0 on success
```

### [`CANReceiver`](can_driver.py)

```python
from hardware.can_driver import CANReceiver

receiver = CANReceiver(
    msgName='engine_ctrl',
    msgID=0x100,
    extendedID=False,
    channel='can0',
    bitrate=500000,
    bustype='socketcan',
    timeout=5,
    recv_timeout=1.0,
)
# Internal thread buffers incoming messages
data = receiver.receive()  # Latest bytes or None
```

---

## Encoder Drivers

### [`EncoderCANDriver`](encoder_driver.py)

Receives encoder values over CAN. Supports multiple encoders per message.

```python
from hardware.encoder_driver import EncoderCANDriver

encoder = EncoderCANDriver(
    msgName="encoder",
    channel="can0",
    msgID=0x200,
    extendedID=False,
    baudrate=500000,
    bustype='socketcan',
    timeout=5
)

# Receive one or more encoder values (float or tuple of floats)
values = encoder.receive(
    num_encoders=2,     # Number of encoders in the CAN message
    float_size=4,       # 4 for float32, 8 for float64
    endianess='little'  # 'little' or 'big'
)
```

### [`EncoderSerialDriver`](encoder_driver.py)

Receives encoder values over Serial.

```python
from hardware.encoder_driver import EncoderSerialDriver

encoder = EncoderSerialDriver(
    msgName="encoder",
    channel="/dev/ttyUSB0",
    msgID=0x12,
    msgIDLength=1,
    baudrate=115200,
    timeout=5
)

# Receive one or more encoder values (float or tuple of floats)
values = encoder.receive(
    num_encoders=2,     # Number of encoders in the message
    float_size=4,       # 4 for float32, 8 for float64
    endianess='little'  # 'little' or 'big'
)
```

---

## IMU Drivers

### [`IMUCANDriver`](imu_driver.py)

Receives IMU data (ax, ay, az, gx, gy, gz) over CAN, each axis on a separate CAN ID.

```python
from hardware.imu_driver import IMUCANDriver

imu = IMUCANDriver(
    msgName="imu",
    msgIDs=[0x200, 0x201, 0x202, 0x203, 0x204, 0x205],  # ax, ay, az, gx, gy, gz
    channel="can0",
    extendedID=False,
    baudrate=500000,
    bustype='socketcan',
    timeout=5
)

# Returns tuple of 6 floats (ax, ay, az, gx, gy, gz)
data = imu.receive(
    float_size=4,       # 4 for float32, 8 for float64
    endianess='little'  # 'little' or 'big'
)
```

### [`IMUSerialDriver`](imu_driver.py)

Receives IMU data (ax, ay, az, gx, gy, gz) over Serial, all axes in one message.

```python
from hardware.imu_driver import IMUSerialDriver

imu = IMUSerialDriver(
    msgName="imu",
    channel="/dev/ttyUSB0",
    msgID=0x10,
    msgIDLength=1,
    baudrate=115200,
    timeout=5
)

# Returns tuple of 6 floats (ax, ay, az, gx, gy, gz)
data = imu.receive(
    float_size=4,       # 4 for float32, 8 for float64
    endianess='little'  # 'little' or 'big'
)
```

---

## Actuators Commands Driver

### [`ActuatorsCommandsDriver`](actuators_commands_driver.py)

High-level driver for sending structured actuator commands over Serial or CAN.

```python
from hardware.actuators_commands_driver import ActuatorsCommandsDriver
from hardware.serial_driver import SerialSender

# Create a low-level sender (SerialSender or CANSender)
sender = SerialSender(
    msgName="actuator_commands",
    channel="/dev/ttyUSB0",
    msgID=0x10,
    msgIDLength=1,
    baudrate=115200,
    timeout=5
)

# Define actuator command structure and names
driver = ActuatorsCommandsDriver(
    driver=sender,
    acutators_commands_struct="bf",     # e.g. uint8 + float32
    actuators_names=["led", "motor"],   # Names for validation
    endianess="little"                  # 'little' or 'big'
)

# Send commands (types must match struct format)
status = driver.send(1, 2.5)
```

**Supported struct format characters:**

| Char | Type         | Size (bytes) |
|------|--------------|--------------|
| b    | int8_t       | 1            |
| B    | uint8_t      | 1            |
| h    | int16_t      | 2            |
| H    | uint16_t     | 2            |
| i    | int32_t      | 4            |
| I    | uint32_t     | 4            |
| q    | int64_t      | 8            |
| Q    | uint64_t     | 8            |
| e    | float16_t    | 2            |
| f    | float32_t    | 4            |
| d    | float64_t    | 8            |
| ?    | bool         | 1            |

---

## Configuration Options

| Parameter        | Description                                              | Default   |
| ---------------- | -------------------------------------------------------- | --------- |
| `msgIDLength`    | Bytes for message-ID header                              | `0`       |
| `msgLenLength`   | Bytes for length header (SPI only)                       | `0`       |
| `baudrate`       | UART baud rate                                           | `115200`  |
| `timeout`        | Seconds for send/receive retries                         | `5`       |
| `mode`           | SPI mode 0–3                                             | `0`       |
| `max_speed_hz`   | SPI clock frequency                                      | `500_000` |
| `packet_size`    | SPI read chunk size                                      | `256`     |
| `extendedID`     | Use 29-bit CAN IDs                                       | `False`   |
| `bitrate`        | CAN bus bitrate (bps)                                    | `250000`  |
| `bustype`        | Python-Can bus type                                      | `socketcan` |
| `recv_timeout`   | CAN receive timeout (seconds)                            | `1.0`     |

---

## Usage Examples

1. **Telemetry over USB**  
   - Use `SerialSender` on MCU to push sensor frames.  
   - Use `SerialReceiver` on PC to collect and log data.
2. **Command & Response via SPI**  
   - Master: `SPISender` writes request with ID+length.  
   - Slave: `SPIReceiver` buffers and dispatches commands.
3. **Vehicle CAN Control**  
   - ECU: `CANSender` transmits control frames.  
   - Monitor: `CANReceiver` logs diagnostic messages.
4. **Encoder Reading**  
   - Use `EncoderCANDriver` or `EncoderSerialDriver` to read wheel or joint positions.
5. **IMU Data Acquisition**  
   - Use `IMUCANDriver` or `IMUSerialDriver` to receive 6-axis IMU data.
6. **Actuator Commanding**  
   - Use `ActuatorsCommandsDriver` to send structured commands to actuators (motors, LEDs, etc).

---

## Logging & Debugging

- All drivers inherit [`LoggingMixin`](logging_mixin.py), producing logs for:
  - Connections (`log_connected`)
  - Sends (`log_sent`)
  - Receives (`log_received`)
  - Errors & Warnings (`log_error`, `log_warning`)
- Logs are written to both console and `hardware.log` in the working directory.
- Inspect `BaseDriver.channelsOperationsInfo` and `instancesInfo` at runtime for stats.

---

## Shutdown & Cleanup

Always call `stop()` or delete the driver to:

- Terminate receiver threads.
- Close underlying ports or buses.

```python
sender.stop()
receiver.stop()
```

Or rely on Python’s garbage collector to invoke `__del__()`.

---

## File Reference

- [base_driver.py](base_driver.py)
- [serial_driver.py](serial_driver.py)
- [spi_driver.py](spi_driver.py)
- [can_driver.py](can_driver.py)
- [encoder_driver.py](encoder_driver.py)
- [imu_driver.py](imu_driver.py)
- [actuators_commands_driver.py](actuators_commands_driver.py)
- [logging_mixin.py](logging_mixin.py)