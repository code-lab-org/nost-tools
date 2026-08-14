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

from .fakes import FakeChannel, wire_broker


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


class TestChannelClosedClearsConnectionState(unittest.TestCase):
    """
    A channel-level failure such as a 403 closes the channel while leaving the
    connection open. The application must stop reporting itself connected, or
    callers are told the wrong thing and send_message() tries to publish through
    a channel that no longer exists.
    """

    def make_closed_channel_app(self):
        app = make_app()
        app._closing = False
        app._reconnect_delay = 15
        return app

    def test_channel_close_clears_connected_flag(self):
        app = self.make_closed_channel_app()
        self.assertTrue(app._is_connected.is_set())

        app.on_channel_closed(app.channel, RuntimeError("ACCESS_REFUSED"))

        self.assertFalse(app._is_connected.is_set())
        self.assertIsNone(app.channel)

    def test_send_message_queues_after_a_channel_close(self):
        app = self.make_closed_channel_app()
        app.on_channel_closed(app.channel, RuntimeError("ACCESS_REFUSED"))

        app.send_message("my_app", "topic", "payload")

        self.assertEqual(len(app._message_queue), 1)


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


def count_stops(ioloop):
    """
    Records stop() calls on one IO loop.

    The counter is bound to the loop object rather than reached through
    app.connection, which reconnect() reassigns partway through.
    """
    ioloop.stop_calls = 0

    def stop():
        ioloop.stop_calls += 1

    ioloop.stop = stop
    return ioloop


class TestConnectionClosed(unittest.TestCase):
    """
    on_connection_closed decides between shutting down and reconnecting.

    Reading the wrong branch is expensive in opposite directions: treating an
    intentional stop as a drop reconnects to a broker the application is done
    with, and treating a drop as intentional strands the application with no
    connection and no retry.
    """

    def make_app(self):
        app = make_app()
        count_stops(app.connection.ioloop)
        app._reconnect_delay = 5
        return app

    def test_the_channel_is_released_on_any_close(self):
        """A stale channel would be published through after the connection is gone."""
        app = self.make_app()
        app._closing = True

        app.on_connection_closed(app.connection, "reason")

        self.assertIsNone(app.channel)

    def test_an_intentional_close_stops_the_loop_without_reconnecting(self):
        app = self.make_app()
        app._closing = True

        app.on_connection_closed(app.connection, "shutting down")

        self.assertEqual(app.connection.ioloop.stop_calls, 1)
        self.assertEqual(app.connection.ioloop.callbacks, [])

    def test_an_unexpected_close_schedules_a_reconnect_instead_of_stopping(self):
        app = self.make_app()
        app._closing = False

        app.on_connection_closed(app.connection, "broker went away")

        self.assertEqual(app.connection.ioloop.stop_calls, 0)
        self.assertEqual(len(app.connection.ioloop.callbacks), 1)
        # The scheduled callback is the reconnect, not something else
        self.assertEqual(app.connection.ioloop.callbacks[0], app.reconnect)


class TestReconnect(unittest.TestCase):
    """
    reconnect builds a fresh connection and hands it to the running IO thread.

    The old loop has to be stopped for the IO thread to pick the new connection
    up, and no second thread may be started, so a reconnect must not leave two
    loops running against two connections.
    """

    def make_app(self, keycloak=False):
        app = make_app()
        app._closing = False
        app._reconnect_delay = 5
        app._connection_parameters = MagicMock()
        app._callbacks_per_topic = {"test.app.status": [object()]}

        config = MagicMock()
        config.rc.server_configuration.servers.rabbitmq.keycloak_authentication = (
            keycloak
        )
        app.config = config

        count_stops(app.connection.ioloop)
        return app

    def test_a_closing_application_does_not_reconnect(self):
        """A reconnect already scheduled when shutdown began must not fire."""
        app = self.make_app()
        app._closing = True
        original = app.connection

        with unittest.mock.patch("pika.SelectConnection") as select_connection:
            app.reconnect()

        # Asserted on the constructor, not on the resulting state: an unguarded
        # reconnect that happens to fail would leave the state untouched too
        select_connection.assert_not_called()
        self.assertIs(app.connection, original)
        self.assertEqual(app.connection.ioloop.stop_calls, 0)

    def test_the_old_loop_is_stopped_so_the_io_thread_takes_the_new_connection(self):
        app = self.make_app()
        old_ioloop = app.connection.ioloop
        created = MagicMock()

        with unittest.mock.patch("pika.SelectConnection", return_value=created):
            app.reconnect()

        self.assertIs(app.connection, created)
        self.assertEqual(old_ioloop.stop_calls, 1)

    def test_topic_callback_tracking_is_reset(self):
        """
        The bindings do not survive the old channel, so tracking that says they
        do would suppress re-subscription on the new one.
        """
        app = self.make_app()

        with unittest.mock.patch("pika.SelectConnection", return_value=MagicMock()):
            app.reconnect()

        self.assertEqual(app._callbacks_per_topic, {})

    def test_a_failed_reconnect_schedules_a_retry(self):
        """
        The IO loop may be stopped at this point, so the retry is scheduled on a
        timer rather than through the loop.
        """
        app = self.make_app()
        timers = []

        class RecordingTimer:
            def __init__(self, delay, callback):
                self.delay, self.callback, self.daemon = delay, callback, False
                timers.append(self)

            def start(self):
                self.started = True

        with unittest.mock.patch("pika.SelectConnection", side_effect=OSError("down")):
            with unittest.mock.patch("threading.Timer", RecordingTimer):
                app.reconnect()

        self.assertEqual(len(timers), 1, "no retry was scheduled")
        self.assertEqual(timers[0].delay, 5)
        self.assertEqual(timers[0].callback, app.reconnect)
        self.assertTrue(timers[0].daemon, "a non-daemon timer would block exit")

    def test_a_token_refresh_failure_still_reconnects(self):
        """
        The existing token may well still be valid, so a refresh failure must not
        cost the application its reconnect.
        """
        app = self.make_app(keycloak=True)
        app.refresh_token = "old-refresh"
        app.new_access_token = MagicMock(side_effect=RuntimeError("keycloak down"))
        created = MagicMock()

        with unittest.mock.patch("pika.SelectConnection", return_value=created):
            app.reconnect()

        self.assertIs(app.connection, created)

    def test_a_refreshed_token_is_used_for_the_new_connection(self):
        app = self.make_app(keycloak=True)
        app.refresh_token = "old-refresh"
        app.new_access_token = MagicMock(return_value=("new-access", "new-refresh"))

        with unittest.mock.patch("pika.SelectConnection", return_value=MagicMock()):
            app.reconnect()

        app.new_access_token.assert_called_once_with("old-refresh")
        self.assertEqual(app.refresh_token, "new-refresh")
        # The token travels as the password, with an empty username
        credentials = app._connection_parameters.credentials
        self.assertEqual(credentials.username, "")
        self.assertEqual(credentials.password, "new-access")


class TestStartUpTransportSecurity(unittest.TestCase):
    """
    start_up builds the pika connection parameters, including the TLS options.

    This is the configuration that closed the certificate validation finding in
    3.2.0, and it had no test. The parameters are saved before the connection is
    attempted, so pointing the application at a socket that never answers lets
    the built parameters be read back without a broker.
    """

    YAML = """
info:
  title: TLS configuration test
  version: '1.0.0'
  description: Points at a port with nothing listening
servers:
  rabbitmq:
    keycloak_authentication: False
    host: "127.0.0.1"
    port: {port}
    tls: {tls}
    {ca_line}
    virtual_host: "/"
    connection_timeout: 1
    connection_attempts: 1
    retry_delay: 1
execution:
  general:
    prefix: tlstest
"""

    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in ("USERNAME", "PASSWORD")}
        os.environ["USERNAME"] = "guest"
        os.environ["PASSWORD"] = "guest"
        self.dead = socket.socket()
        self.dead.bind(("127.0.0.1", 0))
        self.port = self.dead.getsockname()[1]
        self.paths = []

    def tearDown(self):
        self.dead.close()
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        for path in self.paths:
            os.unlink(path)

    def build_parameters(self, tls, ca_cert=None):
        """
        Runs start_up far enough to build the connection parameters.

        Returns the parameters and the cafile that the trust store was built
        from. The connection never completes, so the timeout is expected.
        """
        ca_line = f'tls_ca_cert: "{ca_cert}"' if ca_cert else ""
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        handle.write(self.YAML.format(port=self.port, tls=tls, ca_line=ca_line))
        handle.close()
        self.paths.append(handle.name)

        config = ConnectionConfig(yaml_file=handle.name)
        app = Application("tls_test", setup_signal_handlers=False)

        seen = {}
        real_context = ssl.create_default_context

        def record_context(cafile=None, **kwargs):
            seen["cafile"] = cafile
            return real_context()

        with unittest.mock.patch("ssl.create_default_context", record_context):
            try:
                app.start_up(prefix="tlstest", config=config, set_offset=False)
            except Exception:
                # Reaching the broker is not the point; the parameters are built
                # and saved before the connection is attempted
                pass
        return app._connection_parameters, seen.get("cafile", "not called")

    def test_tls_verifies_the_certificate_against_the_system_trust_store(self):
        """
        With no CA configured the default context is used, which loads the system
        trust store and verifies both the certificate and the hostname.
        """
        parameters, cafile = self.build_parameters(tls="True")

        self.assertIsNotNone(parameters.ssl_options, "TLS was configured but not used")
        self.assertIsNone(cafile, "a trust anchor was passed where none was configured")
        context = parameters.ssl_options.context
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_tls_sends_the_host_for_sni_and_hostname_verification(self):
        parameters, _ = self.build_parameters(tls="True")

        self.assertEqual(parameters.ssl_options.server_hostname, "127.0.0.1")

    def test_a_configured_ca_file_is_used_as_the_trust_anchor(self):
        """A private broker's certificate is trusted through its own CA file."""
        ca = tempfile.NamedTemporaryFile(
            "w", suffix=".pem", delete=False, encoding="utf-8"
        )
        ca.close()
        self.paths.append(ca.name)

        _, cafile = self.build_parameters(tls="True", ca_cert=ca.name)

        self.assertEqual(cafile, ca.name)

    def test_plaintext_leaves_tls_unconfigured(self):
        parameters, cafile = self.build_parameters(tls="False")

        self.assertIsNone(parameters.ssl_options)
        self.assertEqual(cafile, "not called")


class TestStartUpPreAcquiredTokens(unittest.TestCase):
    """
    start_up accepts tokens obtained elsewhere, such as a frontend login.

    The refresh thread renews the session from the refresh token, so an access
    token supplied without one buys a session that dies at the first expiry.
    """

    def make_config(self):
        config = MagicMock()
        # Take the argument branch rather than reading a YAML file
        config.rc.yaml_file = None
        rabbitmq = config.rc.server_configuration.servers.rabbitmq
        rabbitmq.keycloak_authentication = True
        # pika validates these, so they cannot be left as mocks
        rabbitmq.host = "127.0.0.1"
        rabbitmq.port = 5672
        rabbitmq.virtual_host = "/"
        rabbitmq.tls = False
        rabbitmq.locale = "en_US"
        rabbitmq.channel_max = 2047
        rabbitmq.frame_max = 131072
        rabbitmq.heartbeat = 60
        for field in (
            "connection_attempts",
            "retry_delay",
            "socket_timeout",
            "stack_timeout",
            "blocked_connection_timeout",
            "connection_timeout",
            "reconnect_delay",
            "queue_max_size",
        ):
            setattr(rabbitmq, field, 1)
        return config

    def test_an_access_token_without_a_refresh_token_is_rejected(self):
        app = Application("token_test", setup_signal_handlers=False)

        with self.assertRaises(ValueError) as caught:
            app.start_up(
                prefix="tokentest",
                config=self.make_config(),
                set_offset=False,
                access_token="an-access-token",
            )

        self.assertIn("refresh_token is required", str(caught.exception))

    def test_supplied_tokens_skip_the_keycloak_grant(self):
        """Requesting a new grant would discard the session already established."""
        app = Application("token_test", setup_signal_handlers=False)
        app.new_access_token = MagicMock(
            side_effect=AssertionError("a grant was requested")
        )
        app.start_token_refresh_thread = lambda: None

        with unittest.mock.patch("pika.SelectConnection", side_effect=OSError("stop")):
            with self.assertRaises(OSError):
                app.start_up(
                    prefix="tokentest",
                    config=self.make_config(),
                    set_offset=False,
                    access_token="an-access-token",
                    refresh_token="a-refresh-token",
                )

        app.new_access_token.assert_not_called()
        self.assertEqual(app.refresh_token, "a-refresh-token")


class TestDeleteQueues(unittest.TestCase):
    """
    _delete_queues_with_callback removes this application's queues on shutdown.

    Its contract is the completion event: stop_application waits on it for ten
    seconds before giving up, so any path that fails to set it turns a shutdown
    into a ten-second stall. Every failure branch here is really a test that the
    event still gets set.
    """

    def make_app(self, queues=(), exchanges=("test",), fail_ops=()):
        app = wire_broker(
            Application("test_app", setup_signal_handlers=False),
            failing_channel=False,
        )
        app.channel = FakeChannel(fail_ops=fail_ops)
        app.declared_queues = set(queues)
        app.declared_exchanges = set(exchanges)
        return app

    def test_a_closed_channel_signals_completion_rather_than_hanging(self):
        app = self.make_app(queues=["q1"])
        app.channel.is_closed = True
        done = threading.Event()

        app._delete_queues_with_callback(done)

        self.assertTrue(done.is_set())
        self.assertEqual(app.channel.operations, [])

    def test_no_queues_signals_completion_immediately(self):
        app = self.make_app(queues=[])
        done = threading.Event()

        app._delete_queues_with_callback(done)

        self.assertTrue(done.is_set())

    def test_a_queue_is_purged_unbound_and_deleted_in_that_order(self):
        app = self.make_app(queues=["q1"], exchanges=["test"])
        done = threading.Event()

        app._delete_queues_with_callback(done)

        self.assertEqual(
            [name for name, _, _ in app.channel.operations],
            ["purge", "unbind", "delete"],
        )
        self.assertTrue(done.is_set())

    def test_a_deleted_queue_stops_being_tracked(self):
        """Tracking a queue that no longer exists would retry it on the next stop."""
        app = self.make_app(queues=["q1"])
        done = threading.Event()

        app._delete_queues_with_callback(done)

        self.assertEqual(app.declared_queues, set())

    def test_completion_waits_for_every_queue(self):
        """
        Signalling early lets stop_application delete the exchanges out from
        under queues that are still being removed, so the state of the event
        after each deletion is asserted, not just its state at the end.
        """
        app = self.make_app(queues=["q1", "q2", "q3"])
        done = threading.Event()
        set_after_each = []

        original_delete = app.channel.queue_delete

        def recording_delete(queue, **kwargs):
            original_delete(queue, **kwargs)
            set_after_each.append(done.is_set())

        app.channel.queue_delete = recording_delete

        app._delete_queues_with_callback(done)

        self.assertEqual(sorted(app.channel.ops("delete")), ["q1", "q2", "q3"])
        self.assertEqual(set_after_each, [False, False, True])

    def test_a_queue_is_unbound_from_every_exchange(self):
        app = self.make_app(queues=["q1"], exchanges=["ex1", "ex2", "ex3"])
        done = threading.Event()

        app._delete_queues_with_callback(done)

        unbound = {
            detail["exchange"]
            for name, _, detail in app.channel.operations
            if name == "unbind"
        }
        self.assertEqual(unbound, {"ex1", "ex2", "ex3"})

    def test_a_purge_failure_still_deletes_the_queue(self):
        app = self.make_app(queues=["q1"], fail_ops=["purge"])
        done = threading.Event()

        app._delete_queues_with_callback(done)

        self.assertEqual(app.channel.ops("delete"), ["q1"])
        self.assertTrue(done.is_set())

    def test_an_unbind_failure_still_deletes_the_queue(self):
        app = self.make_app(queues=["q1"], fail_ops=["unbind"])
        done = threading.Event()

        app._delete_queues_with_callback(done)

        self.assertEqual(app.channel.ops("delete"), ["q1"])
        self.assertTrue(done.is_set())

    def test_a_delete_failure_still_signals_completion(self):
        """Otherwise a broker-side delete error costs ten seconds of shutdown."""
        app = self.make_app(queues=["q1"], fail_ops=["delete"])
        done = threading.Event()

        app._delete_queues_with_callback(done)

        self.assertTrue(done.is_set())
        self.assertEqual(app.declared_queues, set())


class TestStopApplication(unittest.TestCase):
    """
    stop_application tears down the broker-side resources and the helper threads.

    It runs on every exit, so the properties that matter are that it is safe to
    call twice and that it always finishes.
    """

    def make_app(self, queues=("q1",), predefined=False):
        app = wire_broker(Application("test_app", setup_signal_handlers=False))
        app.channel = FakeChannel()
        app.declared_queues = set(queues)
        app.declared_exchanges = {"test"}
        app.predefined_exchanges_queues = predefined
        # The drain is covered by TestShutdownDrain. Left in place it waits out
        # its own five-second timeout here, because FakeIOLoop records its
        # sentinel callback rather than running it. Counting the calls also
        # gives the idempotence test something to assert on.
        app.drain_calls = 0

        def count_drain(*args, **kwargs):
            app.drain_calls += 1

        app._drain_pending_publishes = count_drain
        return app

    def test_the_second_call_does_nothing(self):
        """
        Shutdown reaches this from both a signal handler and the observer.

        Asserted on the drain, the first statement inside the guard: by the
        second call the queues are already gone, so a repeated run would perform
        no queue operations and leave the recorded operations looking identical.
        """
        app = self.make_app()
        app.stop_application()

        app.stop_application()

        self.assertEqual(app.drain_calls, 1)

    def test_pending_publishes_are_drained_before_the_queues_go(self):
        """
        A message still scheduled when the queue is deleted is lost. The final
        time status is published this way, so the ordering is load-bearing.
        """
        app = self.make_app()
        order = []
        app._drain_pending_publishes = lambda *a, **k: order.append("drain")
        original_delete = app._delete_queues_with_callback

        def record_delete(event):
            order.append("delete_queues")
            original_delete(event)

        app._delete_queues_with_callback = record_delete

        app.stop_application()

        self.assertEqual(order, ["drain", "delete_queues"])

    def test_a_closed_channel_does_not_stall_the_shutdown(self):
        app = self.make_app()
        app.channel.is_closed = True

        started = time.monotonic()
        app.stop_application()
        elapsed = time.monotonic() - started

        # The wait on the cleanup completion event is ten seconds
        self.assertLess(elapsed, 2, "shutdown waited on an event nothing would set")

    def test_helper_threads_are_told_to_stop(self):
        app = self.make_app()

        app.stop_application()

        self.assertTrue(app._should_stop.is_set())

    def test_predefined_topology_is_deleted_through_the_declared_configuration(self):
        """
        Predefined exchanges and queues come from the configuration rather than
        from what this application declared, so a different path removes them.
        """
        app = self.make_app(predefined=True)
        app.channel_configs = [{"queue": "configured"}]
        app.unique_exchanges = {"ex": {}}
        calls = []
        app.delete_queue = lambda configs, name: calls.append(("queue", name))
        app.delete_exchange = lambda exchanges: calls.append(("exchange", exchanges))

        app.stop_application()

        self.assertEqual(calls[0][0], "queue")
        self.assertEqual(calls[1][0], "exchange")


class TestShutDown(unittest.TestCase):
    """
    shut_down is the outermost teardown, ending in os._exit.

    os._exit is patched throughout: unpatched it would take the test runner down
    with it. Everything before that call is ordinary behaviour worth pinning.
    """

    def make_app(self):
        app = wire_broker(Application("test_app", setup_signal_handlers=False))
        app.channel = FakeChannel()
        app.declared_queues = {"q1"}
        app.declared_exchanges = {"test"}
        # See TestStopApplication.make_app: the drain would wait out its timeout
        app._drain_pending_publishes = lambda *args, **kwargs: None
        return app

    def run_shut_down(self, app):
        """Runs shut_down with the process exit captured, returning the exit code."""
        exits = []
        with unittest.mock.patch("os._exit", side_effect=exits.append):
            app.shut_down()
        return exits

    def test_the_process_exits_cleanly(self):
        app = self.make_app()
        self.assertEqual(self.run_shut_down(app), [0])

    def test_the_time_status_publisher_is_detached_from_the_simulator(self):
        """
        The publisher holds a reference to the application, so leaving it
        observing keeps publishing against a connection that is going away.
        """
        app = self.make_app()
        removed = []
        publisher = object()
        app._time_status_publisher = publisher
        app.simulator.remove_observer = removed.append

        self.run_shut_down(app)

        self.assertEqual(removed, [publisher])
        self.assertIsNone(app._time_status_publisher)

    def test_the_connection_is_stopped(self):
        app = self.make_app()
        calls = []
        app.stop_application = lambda: calls.append("stop")

        self.run_shut_down(app)

        self.assertEqual(calls, ["stop"])
        self.assertFalse(app._consuming)

    def test_an_already_closing_application_is_not_stopped_twice(self):
        app = self.make_app()
        app._closing = True
        calls = []
        app.stop_application = lambda: calls.append("stop")

        self.run_shut_down(app)

        self.assertEqual(calls, [])

    def test_background_threads_are_signalled_to_stop(self):
        app = self.make_app()
        app.stop_event = threading.Event()

        self.run_shut_down(app)

        self.assertTrue(app.stop_event.is_set())
        self.assertTrue(app._should_stop.is_set())


if __name__ == "__main__":
    unittest.main()
