"""
Tests for the observers and publisher that connect an application's simulator to
the broker.
"""

import json
import unittest
from datetime import datetime, timedelta, timezone

from nost_tools.application import Application
from nost_tools.application_utils import (
    ModeStatusObserver,
    ShutDownObserver,
    TimeStatusPublisher,
)
from nost_tools.simulator import Mode, Simulator

from .fakes import wire_broker

START = datetime(2020, 1, 1, tzinfo=timezone.utc)


def make_app(connected=True):
    app = wire_broker(
        Application("test_app", setup_signal_handlers=False), connected=connected
    )
    app.app_description = "test description"
    return app


class RecordingApp:
    """Stands in for an Application, recording shut_down calls."""

    def __init__(self):
        self.shut_down_calls = 0

    def shut_down(self):
        self.shut_down_calls += 1


class TestShutDownObserver(unittest.TestCase):
    def test_shuts_down_on_termination(self):
        app = RecordingApp()
        observer = ShutDownObserver(app)

        observer.on_change(
            Simulator, Simulator.PROPERTY_MODE, Mode.TERMINATING, Mode.TERMINATED
        )

        self.assertEqual(app.shut_down_calls, 1)

    def test_ignores_other_mode_transitions(self):
        app = RecordingApp()
        observer = ShutDownObserver(app)

        for new_mode in (Mode.INITIALIZED, Mode.EXECUTING, Mode.PAUSED):
            observer.on_change(
                Simulator, Simulator.PROPERTY_MODE, Mode.UNDEFINED, new_mode
            )

        self.assertEqual(app.shut_down_calls, 0)

    def test_ignores_other_properties(self):
        """A time change reaching TERMINATED as a value must not shut down."""
        app = RecordingApp()
        observer = ShutDownObserver(app)

        observer.on_change(
            Simulator, Simulator.PROPERTY_TIME, START, Mode.TERMINATED
        )

        self.assertEqual(app.shut_down_calls, 0)


class TestTimeStatusPublisher(unittest.TestCase):
    def publish(self, app):
        """Publishes one time status and returns the routing key and parsed body."""
        publisher = TimeStatusPublisher(app, timedelta(seconds=1))
        publisher.publish_message()
        app.connection.ioloop.run_pending()
        return app.channel.routing_keys()[-1], json.loads(app.channel.bodies()[-1])

    def test_publishes_to_the_time_status_topic(self):
        app = make_app()
        app.simulator._time = START
        routing_key, _ = self.publish(app)
        self.assertEqual(routing_key, "test.test_app.status.time")

    def test_message_carries_the_application_identity(self):
        app = make_app()
        app.simulator._time = START
        _, body = self.publish(app)
        self.assertEqual(body["name"], "test_app")
        self.assertEqual(body["description"], "test description")

    def test_message_carries_the_scenario_and_wallclock_times(self):
        app = make_app()
        app.simulator._time = START
        _, body = self.publish(app)
        self.assertEqual(body["properties"]["simTime"], "2020-01-01T00:00:00Z")
        # The wallclock time is read at publish time, so assert it is present and
        # parseable rather than pinning a value
        self.assertIn("time", body["properties"])
        datetime.fromisoformat(body["properties"]["time"].replace("Z", "+00:00"))

    def test_message_is_queued_when_the_connection_is_down(self):
        app = make_app(connected=False)
        app.simulator._time = START

        publisher = TimeStatusPublisher(app, timedelta(seconds=1))
        publisher.publish_message()

        self.assertEqual(app.channel.published, [])
        self.assertEqual(len(app._message_queue), 1)


class TestModeStatusObserver(unittest.TestCase):
    def test_publishes_the_current_mode(self):
        app = make_app()
        observer = ModeStatusObserver(app)

        observer.on_change(
            Simulator, Simulator.PROPERTY_MODE, Mode.UNDEFINED, Mode.INITIALIZED
        )
        app.connection.ioloop.run_pending()

        routing_key = app.channel.routing_keys()[-1]
        body = json.loads(app.channel.bodies()[-1])
        self.assertEqual(routing_key, "test.test_app.status.mode")
        self.assertEqual(body["name"], "test_app")
        # The published mode is read from the simulator, not from new_value
        self.assertEqual(body["properties"]["mode"], app.simulator.get_mode().name)

    def test_ignores_other_properties(self):
        app = make_app()
        observer = ModeStatusObserver(app)

        observer.on_change(Simulator, Simulator.PROPERTY_TIME, START, START)
        app.connection.ioloop.run_pending()

        self.assertEqual(app.channel.published, [])

    def test_a_non_string_prefix_raises_rather_than_publishing(self):
        """
        The prefix becomes the exchange name, so a non-string would fail deeper in
        pika with a less obvious error.
        """
        app = make_app()
        app.prefix = None
        observer = ModeStatusObserver(app)

        with self.assertRaises(ValueError) as caught:
            observer.on_change(
                Simulator, Simulator.PROPERTY_MODE, Mode.UNDEFINED, Mode.INITIALIZED
            )

        self.assertIn("must be a string", str(caught.exception))


class TestModeStatusObserverStopApplication(unittest.TestCase):
    class FakeClosable:
        def __init__(self, is_open=True):
            self.is_open = is_open
            self.closed = False

        def close(self):
            self.closed = True
            self.is_open = False

    def make_observer(self, channel_open=True, connection_open=True):
        app = make_app()
        app.channel = self.FakeClosable(is_open=channel_open)
        app.connection = self.FakeClosable(is_open=connection_open)
        return app, ModeStatusObserver(app)

    def test_closes_an_open_channel_and_connection(self):
        app, observer = self.make_observer()
        observer.stop_application()
        self.assertTrue(app.channel.closed)
        self.assertTrue(app.connection.closed)

    def test_leaves_a_closed_channel_alone(self):
        app, observer = self.make_observer(channel_open=False)
        observer.stop_application()
        self.assertFalse(app.channel.closed)
        self.assertTrue(app.connection.closed)

    def test_leaves_a_closed_connection_alone(self):
        app, observer = self.make_observer(connection_open=False)
        observer.stop_application()
        self.assertTrue(app.channel.closed)
        self.assertFalse(app.connection.closed)


if __name__ == "__main__":
    unittest.main()
