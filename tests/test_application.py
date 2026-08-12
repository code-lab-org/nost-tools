import threading
import time
import unittest

from nost_tools.application import Application

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


if __name__ == "__main__":
    unittest.main()
