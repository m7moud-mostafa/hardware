#!/usr/bin/python3
"""
LoggingMixin class to handle logging inside the hardware package.

Author: Mahmoud Mostafa
Email: mah2002moud@gmail.com
"""

import logging
import os
import sys

class LoggingMixin:
    """
    A mixin class to provide logging functionality for drivers.
    Formats log messages and logs them to both the console and a file.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the LoggingMixin.

        Sets up the logger with handlers for console and file logging.
        """
        super().__init__(*args, **kwargs)
        logger_name = f'hardware.{self.__class__.__name__}.{self.msgName}.server'
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        self.log_file = os.path.join(os.getcwd(), 'hardware.log')
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Define ColoredFormatter for console output
        class ColoredFormatter(logging.Formatter):
            COLORS = {
                'DEBUG': '\033[36m',     # Cyan
                'INFO': '\033[32m',      # Green
                'WARNING': '\033[33m',   # Yellow
                'ERROR': '\033[31m',     # Red
                'CRITICAL': '\033[41m',  # Red background
                'RESET': '\033[0m'
            }

            def format(self, record):
                color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
                message = super().format(record)
                return f"{color}{message}{self.COLORS['RESET']}"

        console_formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Check for existing console handler (StreamHandler but not FileHandler)
        console_handler = None
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                if handler.level == logging.INFO and isinstance(handler.formatter, logging.Formatter):
                    console_handler = handler
                    break

        if not console_handler:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # Check for existing file handler
        file_handler = None
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename == self.log_file:
                file_handler = handler
                break

        if not file_handler:
            file_handler = logging.FileHandler(self.log_file, mode='a')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def log_instance_created(self):
        self.logger.info(f"Instance created: channel={self.msgName}, protocol={self.__class__.__name__}, baudrate:{self.baudrate}")
        self.logger.info(f"Instance message: {self.msgName}, status={self._BaseDriver__isRunning}")
        self.logger.info(f"Running status: {self._BaseDriver__isRunning}")

    def log_status_change(self, status):
        self.logger.info(f"Status change: channel={self.msgName}, status={status}")
        self.logger.info(f"Running status: {self._BaseDriver__isRunning}")

    def log_error(self, error_msg):
        self.logger.error(f"Error msg [{self.numOfMsgs}]: channel={self.msgName}, status={self._BaseDriver__isRunning}, error={error_msg}, Check the logging file {self.log_file}")

    def log_warning(self, warning_msg):
        self.logger.warning(f"Warning msg [{self.numOfMsgs}]: channel={self.msgName}, status={self._BaseDriver__isRunning}, warning={warning_msg}")

    def log_sent(self, message):
        self.logger.info(f"Sent msg [{self.numOfMsgs}]: channel={self.msgName}, msgID={self.msgID} message={message}, status={self._BaseDriver__isRunning}")

    def log_received(self, msg_id, message):
        # Get the BaseDriver class from the instance
        BaseDriver = self.__class__.__bases__[0]  # Gets the first parent class
        
        # Safely get the message count
        numOfMsgs = getattr(BaseDriver, 'channelsOperationsInfo', {}).get(
            self.channel, {}).get(self.operation, {}).get(msg_id, 0)
        
        # Find the matching msgName
        channel_name = self.msgName  # Default to our own msgName if not found
        for msgName, info in getattr(BaseDriver, 'instancesInfo', {}).items():
            if info.get("channel") == self.channel and info.get("id") == msg_id:
                channel_name = msgName
                break
        # Now log it using the instance’s own msgName and status
        self.logger.info(
            f"Received msg [{numOfMsgs}]: "
            f"channel={channel_name}, "
            f"msgID={msg_id}, "
            f"message={message}, "
            f"status={self._BaseDriver__isRunning}"
        )
    def log_stop(self):
        self.logger.info(f"Operation [{self.operation}] stopped for channel={self.msgName} numOfMsgs={self.numOfMsgs}")

    def log_connected(self, port):
        self.logger.info(f"Connected to port={port} for channel={self.msgName}")

    def log_info(self, info):
        self.logger.info(info)