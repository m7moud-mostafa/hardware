import unittest
from unittest.mock import patch
import tempfile
import os
import io
import sys
import logging
import time
from hardware.base_driver import BaseDriver
from hardware.logging_mixin import LoggingMixin

# Define a concrete subclass of BaseDriver for testing
class TestDriver(BaseDriver):
    def connect(self):
        pass

    def disconnect(self):
        pass

    def send(self):
        pass

    def receive(self):
        pass

class TestLoggingMixin(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory and patch os.getcwd for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patcher = patch('os.getcwd', return_value=self.temp_dir.name)
        self.patcher.start()
        
        # Reset logging handlers before each test
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for logger in loggers:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()

    def tearDown(self):
        """Clean up by stopping the patcher and removing the temporary directory."""
        self.patcher.stop()
        
        # Close all handlers and clean up loggers
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for logger in loggers:
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
                
        self.temp_dir.cleanup()

    def test_logger_setup(self):
        """Test that the logger is set up correctly with proper name and handlers."""
        driver = TestDriver(msgName="test_channel", operation="send", msgID=1)
        logger = driver.logger
        self.assertEqual(logger.name, 'hardware.TestDriver.test_channel')
        
        # Get only StreamHandlers that aren't FileHandlers for console
        console_handlers = [h for h in logger.handlers 
                          if isinstance(h, logging.StreamHandler)
                          and not isinstance(h, logging.FileHandler)]
        file_handlers = [h for h in logger.handlers 
                        if isinstance(h, logging.FileHandler)]
        
        self.assertEqual(len(console_handlers), 1, "Should have one console handler")
        self.assertEqual(len(file_handlers), 1, "Should have one file handler")
        
        console_handler = console_handlers[0]
        file_handler = file_handlers[0]
        
        self.assertEqual(console_handler.level, logging.INFO, "Console handler level should be INFO")
        self.assertEqual(file_handler.level, logging.DEBUG, "File handler level should be DEBUG")
        expected_log_file = os.path.join(self.temp_dir.name, 'hardware.log')
        self.assertEqual(file_handler.baseFilename, expected_log_file, "File handler should write to hardware.log in temp dir")

    def test_log_instance_created(self):
        """Test that log_instance_created generates the correct log messages."""
        with self.assertLogs('hardware.TestDriver.test_channel', level='INFO') as cm:
            driver = TestDriver(msgName="test_channel", operation="send", msgID=1)
        self.assertEqual(len(cm.output), 3, "Should log three messages")
        self.assertIn("Instance created: channel=test_channel, protocol=TestDriver", cm.output[0])
        self.assertIn("Instance message: test_channel, status=True", cm.output[1])
        self.assertIn("Running status: True", cm.output[2])

    def test_log_status_change(self):
        """Test that log_status_change logs the correct messages."""
        driver = TestDriver(msgName="test_channel", operation="send", msgID=1)
        with self.assertLogs('hardware.TestDriver.test_channel', level='INFO') as cm:
            driver.log_status_change("new_status")
        self.assertEqual(len(cm.output), 2, "Should log two messages")
        self.assertIn("Status change: channel=test_channel, status=new_status", cm.output[0])
        self.assertIn("Running status: True", cm.output[1])

    def test_log_error(self):
        """Test that log_error logs at ERROR level."""
        driver = TestDriver(msgName="test_channel", operation="send", msgID=1)
        with self.assertLogs('hardware.TestDriver.test_channel', level='ERROR') as cm:
            driver.log_error("Something went wrong")
        self.assertEqual(len(cm.output), 1, "Should log one error message")
        self.assertIn("error=Something went wrong", cm.output[0])
        self.assertIn(f"Check the logging file {driver.log_file}", cm.output[0])

    def test_no_handler_duplication(self):
        """Test that handlers are not duplicated for the same logger."""
        driver1 = TestDriver(msgName="test_channel", operation="send", msgID=1)
        logger = driver1.logger
        self.assertEqual(len(logger.handlers), 2, "Initial instance should have two handlers")
        
        driver2 = TestDriver(msgName="test_channel", operation="send", msgID=1)
        self.assertEqual(len(logger.handlers), 2, "Second instance with same msgName should not add more handlers")

    def test_different_loggers(self):
        """Test that instances with different msgNames have separate loggers."""
        driver1 = TestDriver(msgName="channel1", operation="send", msgID=1)
        driver2 = TestDriver(msgName="channel2", operation="send", msgID=2)
        logger1 = driver1.logger
        logger2 = driver2.logger
        self.assertNotEqual(logger1, logger2, "Loggers should be different for different msgNames")
        self.assertEqual(len(logger1.handlers), 2, "First logger should have two handlers")
        self.assertEqual(len(logger2.handlers), 2, "Second logger should have two handlers")

    def test_info_on_console(self):
        """Test that INFO messages are output to the console."""
        original_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            # Create driver AFTER redirecting stderr
            driver = TestDriver(msgName="test_channel", operation="send", msgID=1)
            driver.logger.info("This is an info message")
            output = sys.stderr.getvalue()
            self.assertIn("This is an info message", output, "INFO messages should appear on console")
        finally:
            sys.stderr = original_stderr

    def test_logs_in_file(self):
        """Test that both DEBUG and INFO messages are written to the log file."""
        driver = TestDriver(msgName="test_channel", operation="send", msgID=1)
        driver.logger.debug("Debug message")
        driver.logger.info("Info message")
        
        # Ensure logs are flushed to the file
        for handler in driver.logger.handlers:
            handler.flush()
        
        log_file_path = os.path.join(self.temp_dir.name, 'hardware.log')
        with open(log_file_path, 'r') as f:
            content = f.read()
        self.assertIn("Debug message", content, "DEBUG message should be in the file")
        self.assertIn("Info message", content, "INFO message should be in the file")

    def test_special_characters(self):
        """Test that messages with special characters are logged correctly."""
        driver = TestDriver(msgName="test_channel", operation="send", msgID=1)
        with self.assertLogs('hardware.TestDriver.test_channel', level='INFO') as cm:
            driver.log_info("Message with\nnewline and 'quotes'")
        self.assertEqual(len(cm.output), 1, "Should log one message")
        self.assertIn("Message with\nnewline and 'quotes'", cm.output[0], "Special characters should be preserved")

    def test_invalid_msgName(self):
        """Test behavior when msgName is invalid."""
        with self.assertRaises(TypeError):
            TestDriver(msgName=None, operation="send", msgID=1)
        with self.assertRaises(TypeError):
            TestDriver(msgName=123, operation="send", msgID=1)
        # Empty msgName should be allowed
        driver = TestDriver(msgName="", operation="send", msgID=1)
        self.assertEqual(driver.logger.name, 'hardware.TestDriver.', "Logger name should handle empty msgName")

    def test_debug_not_on_console(self):
        """Test that DEBUG messages are not output to the console."""
        original_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            driver = TestDriver(msgName="test_channel", operation="send", msgID=1)
            driver.logger.debug("This is a debug message")
            output = sys.stderr.getvalue()
            # Check that the DEBUG message is not present
            self.assertNotIn("This is a debug message", output, 
                            "DEBUG messages should not appear on console")
        finally:
            sys.stderr = original_stderr

if __name__ == '__main__':
    unittest.main()