"""
End-to-end tests against a real RabbitMQ broker.

These cover what the unit tests structurally cannot: that the library declares
exchanges, routes messages, and delivers them over a real AMQP connection.
"""

import json
import os
import threading
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from nost_tools.application import Application
from nost_tools.configuration import ConnectionConfig
from nost_tools.manager import Manager
from nost_tools.managed_application import ManagedApplication

from .broker import (
    requires_broker,
    restore_environment,
    set_broker_credentials,
    write_config,
)

START = datetime(2020, 1, 1, tzinfo=timezone.utc)
STOP = datetime(2020, 1, 2, tzinfo=timezone.utc)


def wait_until(predicate, timeout=20, interval=0.1):
    """Blocks until predicate() is true or the timeout expires. Returns the result."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


class BrokerTestCase(unittest.TestCase):
    """Starts applications against a real broker and tears them down afterwards."""

    def setUp(self):
        self._previous_env = set_broker_credentials()
        # A unique prefix per test keeps concurrent runs and leftover state apart
        self.prefix = f"itest{uuid.uuid4().hex[:8]}"
        self.config_path = write_config(self.prefix)
        self.config = ConnectionConfig(yaml_file=self.config_path)
        self.apps = []

    def tearDown(self):
        for app in self.apps:
            try:
                app.stop_application()
            except Exception:
                pass
        restore_environment(self._previous_env)
        os.unlink(self.config_path)

    def start(self, app):
        """Starts an application and registers it for teardown."""
        self.apps.append(app)
        starter = threading.Thread(
            target=lambda: app.start_up(
                prefix=self.prefix, config=self.config, set_offset=False
            ),
            daemon=True,
        )
        starter.start()
        self.assertTrue(
            wait_until(lambda: app._is_connected.is_set() and app.channel is not None),
            "application did not connect to the broker",
        )
        return app


@requires_broker
class TestPublishSubscribe(BrokerTestCase):
    def test_message_published_by_one_app_reaches_a_subscriber(self):
        received = []

        subscriber = self.start(
            Application("subscriber", setup_signal_handlers=False)
        )
        subscriber.add_message_callback(
            "publisher", "data", lambda ch, method, props, body: received.append(body)
        )
        publisher = self.start(Application("publisher", setup_signal_handlers=False))

        payload = json.dumps({"value": 42})
        publisher.send_message("publisher", "data", payload)

        self.assertTrue(
            wait_until(lambda: received), "subscriber never received the message"
        )
        self.assertEqual(json.loads(received[0]), {"value": 42})

    def test_subscriber_only_receives_its_own_topic(self):
        matched, other = [], []

        subscriber = self.start(
            Application("subscriber", setup_signal_handlers=False)
        )
        subscriber.add_message_callback(
            "publisher", "wanted", lambda ch, m, p, body: matched.append(body)
        )
        publisher = self.start(Application("publisher", setup_signal_handlers=False))

        publisher.send_message("publisher", "unwanted", "no")
        publisher.send_message("publisher", "wanted", "yes")

        self.assertTrue(wait_until(lambda: matched), "wanted topic never arrived")
        time.sleep(1)  # allow an unwanted delivery to arrive if routing is wrong
        self.assertEqual([body.decode() for body in matched], ["yes"])
        self.assertEqual(other, [])

    def test_messages_arrive_in_order(self):
        received = []

        subscriber = self.start(
            Application("subscriber", setup_signal_handlers=False)
        )
        subscriber.add_message_callback(
            "publisher", "seq", lambda ch, m, p, body: received.append(body.decode())
        )
        publisher = self.start(Application("publisher", setup_signal_handlers=False))

        for i in range(10):
            publisher.send_message("publisher", "seq", str(i))

        self.assertTrue(
            wait_until(lambda: len(received) >= 10), f"only received {len(received)}"
        )
        self.assertEqual(received[:10], [str(i) for i in range(10)])


@requires_broker
class TestConcurrentPublishing(BrokerTestCase):
    THREADS = 16
    PAYLOAD_SIZE = 8192
    PACING_SECONDS = 0.002
    DURATION_SECONDS = 4

    def test_concurrent_publishes_do_not_break_the_channel(self):
        """
        Smoke test: sustained publishing from many threads leaves the channel and
        connection healthy and nothing stranded in the retry queue.

        This is NOT a reliable regression guard for the 505 UNEXPECTED_FRAME
        defect. Against a plaintext localhost broker the frame interleaving is
        timing dependent and does not surface consistently; the defect was only
        reproduced deterministically over TLS against a remote broker. The
        deterministic guard is the unit test asserting that send_message()
        schedules onto the IO thread rather than publishing inline, which is the
        client-side property that actually causes the interleaving.

        What this test does cover is that concurrent publishing works end to end
        over a real AMQP connection, which no unit test can show.
        """
        publisher = self.start(Application("publisher", setup_signal_handlers=False))

        stop = threading.Event()
        errors = []

        def worker(index):
            while not stop.is_set():
                time.sleep(self.PACING_SECONDS)
                try:
                    publisher.send_message(
                        "publisher", f"w{index}", "x" * self.PAYLOAD_SIZE
                    )
                except Exception as e:  # pragma: no cover - only on regression
                    errors.append(e)
                    return

        threads = [
            threading.Thread(target=worker, args=(i,), daemon=True)
            for i in range(self.THREADS)
        ]
        for thread in threads:
            thread.start()
        time.sleep(self.DURATION_SECONDS)
        stop.set()
        for thread in threads:
            thread.join(timeout=5)

        # Allow scheduled publishes to drain before inspecting the connection
        time.sleep(2)
        self.assertEqual(errors, [])
        self.assertIsNotNone(
            publisher.channel, "channel was destroyed during concurrent publishing"
        )
        self.assertTrue(publisher._is_connected.is_set())
        self.assertEqual(
            len(publisher._message_queue),
            0,
            "messages were queued, indicating the channel was lost",
        )


@requires_broker
class TestManagerProtocol(BrokerTestCase):
    def test_managed_application_reports_ready_after_an_init_command(self):
        """Exercises the manager protocol across two real connections."""
        managed = self.start(
            ManagedApplication("testapp", setup_signal_handlers=False)
        )
        manager = Manager("manager", setup_signal_handlers=False)
        manager.required_apps_status = {"testapp": False}
        self.start(manager)

        manager.add_message_callback(
            "testapp", "status.ready", manager.on_app_ready_status
        )
        managed.add_message_callback("manager", "init", managed.on_manager_init)
        time.sleep(1)  # let both subscriptions bind before publishing

        manager.init(START, STOP, required_apps=["testapp"])

        self.assertTrue(
            wait_until(lambda: manager.required_apps_status.get("testapp")),
            "manager never observed the application as ready",
        )
        self.assertEqual(managed._sim_start_time, START)
        self.assertEqual(managed._sim_stop_time, STOP)


if __name__ == "__main__":
    unittest.main()
