import os
import socket
import ssl
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock

from nost_tools.application import Application
from nost_tools.configuration import ConnectionConfig
from nost_tools.errors import ConnectionTimeoutError

from .fakes import wire_broker


def make_app(connected=True, queue_max_size=100, failing_channel=False):
    """Builds an Application wired to broker doubles, bypassing start_up()."""
    return wire_broker(
        Application("test_app", setup_signal_handlers=False),
        connected=connected,
        queue_max_size=queue_max_size,
        failing_channel=failing_channel,
    )


class TestSendMessage(unittest.TestCase):
    def test_publishes_with_correct_exchange_routing_key_and_body(self):
        app = make_app()
        app.send_message(app_name="my_app", app_topics="status.ready", payload="hello")

        # Nothing is published until the IO loop runs the scheduled callback
        self.assertEqual(app.channel.published, [])
        app.connection.ioloop.run_pending()

        self.assertEqual(
            app.channel.published, [("test", "test.my_app.status.ready", "hello")]
        )

    def test_list_of_topics_produces_one_publish_each(self):
        app = make_app()
        app.send_message(
            app_name="my_app", app_topics=["alpha", "beta", "gamma"], payload="payload"
        )
        app.connection.ioloop.run_pending()

        routing_keys = [routing_key for _, routing_key, _ in app.channel.published]
        self.assertEqual(
            routing_keys,
            ["test.my_app.alpha", "test.my_app.beta", "test.my_app.gamma"],
        )

    def test_publish_is_scheduled_not_performed_inline(self):
        """The 505 UNEXPECTED_FRAME guard: send_message must never publish directly."""
        app = make_app()
        app.send_message(app_name="my_app", app_topics="topic", payload="payload")

        self.assertEqual(app.channel.publish_threads, [])
        self.assertEqual(len(app.connection.ioloop.callbacks), 1)

        app.connection.ioloop.run_pending()
        self.assertEqual(len(app.channel.publish_threads), 1)


class TestQueueing(unittest.TestCase):
    def test_message_is_queued_when_connection_is_down(self):
        app = make_app(connected=False)
        app.send_message(app_name="my_app", app_topics="topic", payload="payload")

        self.assertEqual(len(app._message_queue), 1)
        self.assertEqual(app.channel.published, [])
        self.assertEqual(app.connection.ioloop.callbacks, [])

    def test_message_is_dropped_when_queue_is_full(self):
        app = make_app(connected=False, queue_max_size=2)
        for i in range(4):
            app.send_message(app_name="my_app", app_topics="topic", payload=f"m{i}")

        self.assertEqual(len(app._message_queue), 2)
        payloads = [payload for _, _, _, payload in app._message_queue]
        self.assertEqual(payloads, ["m0", "m1"])

    def test_queued_messages_flush_in_fifo_order_on_reconnect(self):
        app = make_app(connected=False)
        for i in range(3):
            app.send_message(app_name="my_app", app_topics="topic", payload=f"m{i}")
        self.assertEqual(len(app._message_queue), 3)

        # Connection restored, then a new message triggers queue processing
        app._is_connected.set()
        app.send_message(app_name="my_app", app_topics="topic", payload="m3")
        app.connection.ioloop.run_pending()

        bodies = [body for _, _, body in app.channel.published]
        self.assertEqual(bodies, ["m0", "m1", "m2", "m3"])
        self.assertEqual(app._message_queue, [])

    def test_failed_publish_requeues_with_original_timestamp(self):
        app = make_app(failing_channel=True)
        app.send_message(app_name="my_app", app_topics="topic", payload="payload")

        scheduled_at = None
        for callback in app.connection.ioloop.callbacks:
            scheduled_at = callback.args[0]
        app.connection.ioloop.run_pending()

        self.assertEqual(len(app._message_queue), 1)
        requeued_timestamp = app._message_queue[0][0]
        self.assertEqual(requeued_timestamp, scheduled_at)

    def test_requeue_preserves_ordering_against_newer_messages(self):
        """A re-queued message must still sort ahead of one submitted later."""
        app = make_app(failing_channel=True)
        app.send_message(app_name="my_app", app_topics="topic", payload="first")
        app.connection.ioloop.run_pending()

        app._is_connected.clear()
        app.send_message(app_name="my_app", app_topics="topic", payload="second")

        payloads = [payload for _, _, _, payload in sorted(app._message_queue)]
        self.assertEqual(payloads, ["first", "second"])


class TestShutdownDrain(unittest.TestCase):
    def test_drain_runs_pending_publishes_before_shutdown(self):
        app = make_app()
        app.send_message(app_name="my_app", app_topics="topic", payload="payload")
        self.assertEqual(app.channel.published, [])

        # The drain schedules a sentinel; the IO loop runs everything ahead of it
        drain_thread = threading.Thread(
            target=app._drain_pending_publishes, kwargs={"timeout": 5.0}
        )
        drain_thread.start()
        while not app.connection.ioloop.callbacks:
            pass
        app.connection.ioloop.run_pending()
        drain_thread.join(timeout=5)

        self.assertFalse(drain_thread.is_alive())
        self.assertEqual(len(app.channel.published), 1)

    def test_drain_returns_immediately_when_connection_is_closed(self):
        app = make_app()
        app.connection.is_closed = True

        started = time.monotonic()
        app._drain_pending_publishes(timeout=5.0)
        elapsed = time.monotonic() - started

        # Returns without waiting out the timeout, and schedules no sentinel
        self.assertLess(elapsed, 1.0)
        self.assertEqual(app.connection.ioloop.callbacks, [])

    def test_drain_does_not_deadlock_when_called_on_io_thread(self):
        app = make_app()
        app._io_thread = threading.current_thread()
        app._drain_pending_publishes(timeout=5.0)  # must not block
        self.assertEqual(app.connection.ioloop.callbacks, [])


class TestConnectionErrorHandling(unittest.TestCase):
    def test_certificate_failure_logs_actionable_guidance(self):
        """
        A verification failure must name the setting that fixes it. Without this
        a self-hosted broker produces a bare OpenSSL error and a support ticket.
        """
        app = make_app()
        app.config = MagicMock()
        app.config.rc.server_configuration.servers.rabbitmq.host = "broker.example.edu"
        app.config.rc.server_configuration.servers.rabbitmq.port = 5671

        with self.assertLogs("nost_tools.application", level="ERROR") as captured:
            app.on_connection_error(
                None,
                ssl.SSLCertVerificationError(
                    "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed"
                ),
            )

        guidance = "\n".join(captured.output)
        self.assertIn("tls_ca_cert", guidance)
        self.assertIn("subjectAltName", guidance)
        self.assertIn("broker.example.edu", guidance)

    def test_unrelated_connection_error_omits_certificate_guidance(self):
        app = make_app()
        app.config = MagicMock()

        with self.assertLogs("nost_tools.application", level="ERROR") as captured:
            app.on_connection_error(None, ConnectionRefusedError("Connection refused"))

        self.assertNotIn("tls_ca_cert", "\n".join(captured.output))

    def test_connection_error_clears_the_connected_flag(self):
        app = make_app()
        app.config = MagicMock()
        self.assertTrue(app._is_connected.is_set())

        app.on_connection_error(None, ConnectionRefusedError("Connection refused"))

        self.assertFalse(app._is_connected.is_set())


class TestChannelLevelFailure(unittest.TestCase):
    def test_send_message_queues_when_the_channel_is_gone(self):
        """
        A channel-level failure such as a 403 leaves _is_connected set while the
        channel is torn down, so the application reports itself connected with no
        way to publish. Messages must be queued rather than lost or raised.
        """
        app = make_app()
        app.channel = None  # _is_connected deliberately left set

        app.send_message("repro", "topic", "payload")

        self.assertEqual(len(app._message_queue), 1)
        self.assertEqual(app.connection.ioloop.callbacks, [])


class TestStartUpConnectionTimeout(unittest.TestCase):
    """
    start_up() previously waited on _is_connected with no timeout, so a broker
    that never answered left the application hanging with no indication of why.
    """

    YAML = """
info:
  title: Connection timeout test
  version: '1.0.0'
  description: Points at a port with nothing listening
servers:
  rabbitmq:
    keycloak_authentication: False
    host: "127.0.0.1"
    port: {port}
    tls: False
    virtual_host: "/"
    connection_timeout: 2
    connection_attempts: 1
    retry_delay: 1
execution:
  general:
    prefix: timeouttest
"""

    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in ("USERNAME", "PASSWORD")}
        os.environ["USERNAME"] = "guest"
        os.environ["PASSWORD"] = "guest"
        # Bind a socket without listening, so connections hang rather than being
        # refused; a refused connection would fail faster than the timeout path
        self.dead = socket.socket()
        self.dead.bind(("127.0.0.1", 0))
        self.port = self.dead.getsockname()[1]

        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        handle.write(self.YAML.format(port=self.port))
        handle.close()
        self.config_path = handle.name

    def tearDown(self):
        self.dead.close()
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        os.unlink(self.config_path)

    def test_start_up_raises_instead_of_hanging(self):
        config = ConnectionConfig(yaml_file=self.config_path)
        app = Application("timeout_test", setup_signal_handlers=False)

        started = time.monotonic()
        with self.assertRaises(ConnectionTimeoutError) as caught:
            app.start_up(prefix="timeouttest", config=config, set_offset=False)
        elapsed = time.monotonic() - started

        # Returns near the configured timeout rather than blocking indefinitely
        self.assertLess(elapsed, 20)
        message = str(caught.exception)
        self.assertIn("connection_timeout", message)
        self.assertIn(str(self.port), message)

    def test_timeout_error_is_catchable_as_connection_error(self):
        self.assertTrue(issubclass(ConnectionTimeoutError, ConnectionError))


if __name__ == "__main__":
    unittest.main()
