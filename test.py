#!/usr/bin/env python3
"""
steering_angle_sender.py

This script sends a simulated steering angle to Arduino.
Message structure: [1 byte msgID=0x10] + [4 bytes float]
"""

import time
from hardware.serial_driver import SerialSender  # your module path for SerialSender

def main():
    # Create a unique sender for steering angle with msgID 0x10.
    sender = SerialSender("actuator", "/dev/ttyACM0", msgID=0x10, msgIDLength=1, baudrate=9600)
    time.sleep(2)  # Wait for Arduino initialization

    count = 0
    while True:
        # Simulate a steering angle change (wrap-around at 360 degrees)
        data = count % 2
        data_bytes = data.to_bytes()
        status = sender.send(data_bytes)
        if status == 0:
            print(f"Sent acuator (id 0x10): {data}")
            count += 1
        else:
            print("Failed to send led")

        time.sleep(1)

if __name__ == "__main__":
    main()
