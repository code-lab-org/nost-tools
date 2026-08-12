"""
Tests for how a ManagedApplication responds to commands published by a Manager.

Command callbacks run on the IO thread when a message arrives, so they are invoked
directly here with the payloads a Manager would publish.
"""

import json
import threading
import unittest
from datetime import datetime, timedelta, timezone

from nost_tools.managed_application import ManagedApplication
from nost_tools.schemas import InitCommand, StopCommand, UpdateCommand
from nost_tools.simulator import Mode

from .fakes import wait_for, wait_for_mode, wire_broker

START = datetime(2020, 1, 1, tzinfo=timezone.utc)
STOP = datetime(2020, 1, 2, tzinfo=timezone.utc)


class FakeMethod:
    """Stands in for pika's Basic.Deliver frame."""

    def __init__(self, routing_key="test.manager.init"):
        self.routing_key = routing_key


def make_managed_app(connected=True):
    app = ManagedApplication("test_app", setup_signal_handlers=False)
    return wire_broker(app, connected=connected)


def init_payload(required_apps=None):
    return InitCommand.model_validate(
        {
            "taskingParameters": {
                "simStartTime": START,
                "simStopTime": STOP,
                "requiredApps": required_apps or [],
            }
        }
    ).model_dump_json(by_alias=True).encode("utf-8")


class TestInitCommand(unittest.TestCase):
    def test_init_records_the_scenario_window(self):
        app = make_managed_app()
        app.on_manager_init(None, FakeMethod(), None, init_payload())
        self.assertEqual(app._sim_start_time, START)
        self.assertEqual(app._sim_stop_time, STOP)

    def test_init_publishes_ready_status(self):
        app = make_managed_app()
        app.on_manager_init(None, FakeMethod(), None, init_payload())
        app.connection.ioloop.run_pending()

        self.assertEqual(len(app.channel.published), 1)
        routing_key = app.channel.routing_keys()[0]
        self.assertTrue(routing_key.endswith("status.ready"))

        body = json.loads(app.channel.bodies()[0])
        self.assertEqual(body["name"], "test_app")
        self.assertTrue(body["properties"]["ready"])

    def test_malformed_init_payload_does_not_raise(self):
        """A bad command must not tear down the application's IO thread."""
        app = make_managed_app()
        app.on_manager_init(None, FakeMethod(), None, b"not json")
        self.assertIsNone(app._sim_start_time)


def stop_payload(sim_stop_time):
    return (
        StopCommand.model_validate({"taskingParameters": {"simStopTime": sim_stop_time}})
        .model_dump_json(by_alias=True)
        .encode("utf-8")
    )


class TestStopCommand(unittest.TestCase):
    def test_stop_shortens_the_run_while_executing(self):
        app = make_managed_app()
        new_stop = START + timedelta(hours=6)

        thread = threading.Thread(
            target=app.simulator.execute,
            kwargs={
                "init_time": START,
                "duration": STOP - START,
                "time_step": timedelta(seconds=1),
                "time_scale_factor": 10000,
            },
            daemon=True,
        )
        thread.start()
        wait_for_mode(self, app.simulator, Mode.EXECUTING)

        app.on_manager_stop(None, FakeMethod("test.manager.stop"), None,
                            stop_payload(new_stop))

        # set_end_time converts to a duration relative to the init time
        wait_for(
            self,
            lambda: app.simulator.get_duration() == new_stop - START,
            "duration to shorten",
        )
        wait_for_mode(self, app.simulator, Mode.TERMINATED)

    def test_stop_before_execution_is_logged_not_raised(self):
        """
        set_end_time requires EXECUTING. A stop arriving early must be swallowed so
        the IO thread survives, rather than propagating out of the callback.
        """
        app = make_managed_app()
        app.on_manager_stop(None, FakeMethod("test.manager.stop"), None,
                            stop_payload(STOP))
        self.assertEqual(app.simulator.get_mode(), Mode.UNDEFINED)


class TestUpdateCommand(unittest.TestCase):
    def test_update_is_deferred_until_the_simulator_is_executing(self):
        """
        The manager may publish an update before execution begins; applying it to
        an idle simulator would raise, so it must be scheduled rather than applied.
        """
        app = make_managed_app()
        payload = (
            UpdateCommand.model_validate(
                {
                    "taskingParameters": {
                        "timeScalingFactor": 25.0,
                        "simUpdateTime": START + timedelta(hours=1),
                    }
                }
            )
            .model_dump_json(by_alias=True)
            .encode("utf-8")
        )
        self.assertEqual(app.simulator.get_mode(), Mode.UNDEFINED)
        app.on_manager_update(None, FakeMethod("test.manager.update"), None, payload)
        # Does not raise, and the idle simulator is left alone
        self.assertEqual(app.simulator.get_mode(), Mode.UNDEFINED)


class TestReadyStatus(unittest.TestCase):
    def test_ready_publishes_to_the_status_ready_topic(self):
        app = make_managed_app()
        app.ready()
        app.connection.ioloop.run_pending()

        self.assertEqual(len(app.channel.published), 1)
        self.assertTrue(app.channel.routing_keys()[0].endswith("status.ready"))

    def test_ready_is_queued_when_the_connection_is_down(self):
        app = make_managed_app(connected=False)
        app.ready()
        self.assertEqual(app.channel.published, [])
        self.assertEqual(len(app._message_queue), 1)


if __name__ == "__main__":
    unittest.main()
