"""
Tests for the logger application's file handling and message recording.
"""

import os
import tempfile
import unittest

from nost_tools.logger_application import LoggerApplication


class FakeMethod:
    """Stands in for pika's Basic.Deliver frame."""

    def __init__(self, routing_key):
        self.routing_key = routing_key


class TestLogFileHandling(unittest.TestCase):
    def setUp(self):
        self.log_dir = tempfile.mkdtemp()
        self.app = LoggerApplication("test_logger")
        self.app.log_dir = self.log_dir

    def tearDown(self):
        self.app._close_log_file()
        for name in os.listdir(self.log_dir):
            os.unlink(os.path.join(self.log_dir, name))
        os.rmdir(self.log_dir)

    def log_contents(self):
        name = os.listdir(self.log_dir)[0]
        with open(os.path.join(self.log_dir, name), encoding="utf-8") as handle:
            return handle.read()

    def test_opening_writes_a_csv_header(self):
        self.app._open_log_file()
        self.app.log_file.flush()
        self.assertEqual(self.log_contents().splitlines()[0], "Timestamp,Topic,Payload")

    def test_opening_twice_closes_the_previous_file(self):
        self.app._open_log_file()
        first = self.app.log_file
        self.app._open_log_file()
        self.assertTrue(first.closed)
        self.assertFalse(self.app.log_file.closed)

    def test_closing_clears_the_handle(self):
        self.app._open_log_file()
        handle = self.app.log_file
        self.app._close_log_file()
        self.assertTrue(handle.closed)
        self.assertIsNone(self.app.log_file)

    def test_closing_when_not_open_is_a_no_op(self):
        self.assertIsNone(self.app.log_file)
        self.app._close_log_file()
        self.assertIsNone(self.app.log_file)


class TestMessageLogging(unittest.TestCase):
    def setUp(self):
        self.log_dir = tempfile.mkdtemp()
        self.app = LoggerApplication("test_logger")
        self.app.log_dir = self.log_dir

    def tearDown(self):
        self.app._close_log_file()
        for name in os.listdir(self.log_dir):
            os.unlink(os.path.join(self.log_dir, name))
        os.rmdir(self.log_dir)

    def log_lines(self):
        name = os.listdir(self.log_dir)[0]
        with open(os.path.join(self.log_dir, name), encoding="utf-8") as handle:
            return handle.read().splitlines()

    def test_message_is_recorded_with_topic_and_payload(self):
        self.app._open_log_file()
        self.app.on_log_message(
            None, FakeMethod("test.planner.selected"), None, b'{"value": 1}'
        )

        line = self.log_lines()[1]
        self.assertIn("test.planner.selected", line)
        self.assertIn('{"value": 1}', line)

    def test_string_payloads_are_accepted(self):
        self.app._open_log_file()
        self.app.on_log_message(None, FakeMethod("test.topic"), None, "plain text")
        self.assertIn("plain text", self.log_lines()[1])

    def test_a_closed_file_is_reopened_rather_than_dropping_the_message(self):
        """
        A message arriving with no open file must not be lost silently; the logger
        reopens rather than discarding.
        """
        self.assertIsNone(self.app.log_file)
        self.app.on_log_message(None, FakeMethod("test.topic"), None, b"payload")
        self.assertIsNotNone(self.app.log_file)

    def test_undecodable_payload_does_not_raise(self):
        """A bad payload must not tear down the logger's IO thread."""
        self.app._open_log_file()
        self.app.on_log_message(
            None, FakeMethod("test.topic"), None, b"\xff\xfe invalid"
        )
        self.assertIsNotNone(self.app.log_file)


if __name__ == "__main__":
    unittest.main()
