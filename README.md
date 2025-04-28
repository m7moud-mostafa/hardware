# Hardware Drivers Package

This document describes how to use the Serial, SPI, and CAN drivers provided in this hardware package. It covers initialization, configuration, sending, receiving, and shutdown for USB/UART (Serial), SPI, and CAN buses.

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [BaseDriver Highlights](#basedriver-highlights)
4. [Serial Drivers](#serial-drivers)
   - [SerialSender](#serialsender)
   - [SerialReceiver](#serialreceiver)
5. [SPI Drivers](#spi-drivers)
   - [SPISender](#spisender)
   - [SPIReceiver](#spireceiver)
6. [CAN Drivers](#can-drivers)
   - [CANSender](#cansender)
   - [CANReceiver](#canreceiver)
7. [Configuration Options](#configuration-options)
8. [Usage Examples](#usage-examples)
9. [Logging & Debugging](#logging--debugging)
10. [Shutdown & Cleanup](#shutdown--cleanup)

---

## Overview

The hardware package includes three communication layers:

- **Serial drivers** for USB/UART ports.
- **SPI drivers** for SPI bus devices.
- **CAN drivers** for CAN bus devices.

Each layer provides both sender and receiver subclasses, inheriting from a common `BaseDriver` that handles:

- Automatic connection retries
- Threaded receive loops
- Message‐ID framing
- Buffer‐overflow detection & cleanup
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

All drivers extend `hardware.base_driver.BaseDriver`, which provides:

- `send(data: bytes) -> int`
- `receive() -> bytes`
- Automatic retry in `_try_to_connect()`
- `stop()` for graceful shutdown
- Class attributes:
  - `instancesInfo` (per‐driver metadata)
  - `channelsOperationsInfo` (counters & buffer stats)
  - `receivedMsgsBuffer` (shared receive buffers)

---

## Serial Drivers

### SerialSender

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

### SerialReceiver

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

### SPISender

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

### SPIReceiver

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

### CANSender

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

### CANReceiver

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

## Configuration Options

| Parameter        | Description                                              | Default   |
| ---------------- | -------------------------------------------------------- | --------- |
| `msgIDLength`    | Bytes for message‐ID header                              | `0`       |
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

---

## Logging & Debugging

- All drivers inherit `LoggingMixin`, producing logs for:
  - Connections (`log_connected`)
  - Sends (`log_sent`)
  - Receives (`log_received`)
  - Errors & Warnings (`log_error`, `log_warning`)

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
