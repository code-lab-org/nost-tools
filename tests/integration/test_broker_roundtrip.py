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
from nost_tools.simulator import Mode

from .broker import (
    write_scenario_config,
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

    def wait_for_subscription(
        self, publisher, received, app_name, topic, timeout=15
    ):
        """
        Publishes probe messages until one arrives, confirming the binding is live.

        add_message_callback() issues queue_bind asynchronously on the IO thread,
        so a message published immediately after registering a callback can reach
        the exchange before the queue is bound, match no binding, and be silently
        discarded. Waiting on a real round trip is deterministic, unlike guessing
        a delay long enough for the bind to complete.

        Clears `received` before returning so probes do not pollute assertions.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            publisher.send_message(app_name, topic, "__probe__")
            if wait_until(lambda: received, timeout=1):
                received.clear()
                return
        self.fail(f"subscription to {app_name}.{topic} never became active")


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
        self.wait_for_subscription(publisher, received, "publisher", "data")

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
        self.wait_for_subscription(publisher, matched, "publisher", "wanted")

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
        self.wait_for_subscription(publisher, received, "publisher", "seq")

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

        # Both bindings must be live: the manager's init command has to reach the
        # managed application, and its ready status has to reach the manager
        probes = []
        managed.add_message_callback(
            "manager", "probe", lambda ch, m, p, body: probes.append(body)
        )
        self.wait_for_subscription(manager, probes, "manager", "probe")

        manager.init(START, STOP, required_apps=["testapp"])

        self.assertTrue(
            wait_until(lambda: manager.required_apps_status.get("testapp")),
            "manager never observed the application as ready",
        )
        self.assertEqual(managed._sim_start_time, START)
        self.assertEqual(managed._sim_stop_time, STOP)


@requires_broker
class TestFullTestPlan(BrokerTestCase):
    """
    Drives a complete test plan through `_execute_test_plan_impl` against a real
    broker: parameters read from YAML, initialize, wait for readiness, start,
    execute, and stop.

    The unit tests substitute a simulator whose clock the test controls, which
    lets them assert sequencing but not that the orchestration works against a
    real broker with a real simulator. This covers that.
    """

    def test_manager_drives_a_scenario_from_start_to_stop(self):
        config_path = write_scenario_config(self.prefix, "testapp")
        self.addCleanup(os.unlink, config_path)
        config = ConnectionConfig(yaml_file=config_path)

        managed = ManagedApplication("testapp", setup_signal_handlers=False)
        self.apps.append(managed)
        threading.Thread(
            target=lambda: managed.start_up(
                prefix=self.prefix, config=config, set_offset=False
            ),
            daemon=True,
        ).start()
        self.assertTrue(
            wait_until(
                lambda: managed._is_connected.is_set() and managed.channel is not None
            ),
            "managed application did not connect",
        )

        manager = Manager("manager", setup_signal_handlers=False)
        self.apps.append(manager)
        threading.Thread(
            target=lambda: manager.start_up(
                prefix=self.prefix, config=config, set_offset=False
            ),
            daemon=True,
        ).start()
        self.assertTrue(
            wait_until(
                lambda: manager._is_connected.is_set() and manager.channel is not None
            ),
            "manager did not connect",
        )

        # Let both applications' subscriptions bind before commanding
        time.sleep(2)

        manager.execute_test_plan()

        self.assertTrue(
            wait_until(
                lambda: manager.required_apps_status.get("testapp"), timeout=30
            ),
            "manager never observed the application as ready",
        )
        self.assertTrue(
            wait_until(
                lambda: managed.simulator.get_mode()
                in (Mode.EXECUTING, Mode.TERMINATING, Mode.TERMINATED),
                timeout=30,
            ),
            f"application never executed (mode {managed.simulator.get_mode()})",
        )
        self.assertTrue(
            wait_until(
                lambda: managed.simulator.get_mode() == Mode.TERMINATED, timeout=60
            ),
            f"application never terminated (mode {managed.simulator.get_mode()})",
        )

        # The scenario window from the YAML file reached the application
        self.assertEqual(
            managed._sim_start_time,
            datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(
            managed._sim_stop_time,
            datetime(2020, 1, 1, 0, 1, tzinfo=timezone.utc),
        )


if __name__ == "__main__":
    unittest.main()
