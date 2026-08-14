"""
Tests for the commands a Manager publishes and the application status it tracks.

Commands are published through send_message(), which schedules onto the IO thread,
so tests drain the recorded callbacks before inspecting what reached the channel.
"""

import json
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone

from nost_tools.manager import Manager
from nost_tools.schemas import ReadyStatus

from .fakes import wire_broker

START = datetime(2020, 1, 1, tzinfo=timezone.utc)
STOP = datetime(2020, 1, 2, tzinfo=timezone.utc)


class FakeMethod:
    """Stands in for pika's Basic.Deliver frame."""

    def __init__(self, routing_key):
        self.routing_key = routing_key


def make_manager(connected=True):
    return wire_broker(
        Manager("test_manager", setup_signal_handlers=False), connected=connected
    )


def published_command(app):
    """Drains scheduled publishes and returns (routing_key, parsed body)."""
    app.connection.ioloop.run_pending()
    routing_key = app.channel.routing_keys()[-1]
    return routing_key, json.loads(app.channel.bodies()[-1])


class TestInitCommand(unittest.TestCase):
    def test_init_publishes_the_scenario_window_and_required_apps(self):
        manager = make_manager()
        manager.init(START, STOP, required_apps=["planner", "simulator"])

        routing_key, body = published_command(manager)
        self.assertTrue(routing_key.endswith("init"))
        params = body["taskingParameters"]
        self.assertEqual(params["simStartTime"], "2020-01-01T00:00:00Z")
        self.assertEqual(params["simStopTime"], "2020-01-02T00:00:00Z")
        self.assertEqual(params["requiredApps"], ["planner", "simulator"])

    def test_init_defaults_to_no_required_apps(self):
        manager = make_manager()
        manager.init(START, STOP)
        _, body = published_command(manager)
        self.assertEqual(body["taskingParameters"]["requiredApps"], [])


class TestStopCommand(unittest.TestCase):
    def test_stop_publishes_the_stop_time(self):
        manager = make_manager()
        manager.stop(STOP)

        routing_key, body = published_command(manager)
        self.assertTrue(routing_key.endswith("stop"))
        self.assertEqual(
            body["taskingParameters"]["simStopTime"], "2020-01-02T00:00:00Z"
        )


class TestUpdateCommand(unittest.TestCase):
    def test_update_publishes_the_new_time_scale_factor(self):
        """
        update() publishes before applying the change to its own simulator, which
        requires EXECUTING. Called while idle it raises, but the command has
        already gone out to every application by then.
        """
        manager = make_manager()
        update_time = START + timedelta(hours=2)

        with self.assertRaises(RuntimeError):
            manager.update(30.0, update_time)

        routing_key, body = published_command(manager)
        self.assertTrue(routing_key.endswith("update"))
        params = body["taskingParameters"]
        self.assertEqual(params["timeScalingFactor"], 30.0)
        self.assertEqual(params["simUpdateTime"], "2020-01-01T02:00:00Z")


class TestReadyStatusTracking(unittest.TestCase):
    def ready_payload(self, name, ready=True):
        return (
            ReadyStatus.model_validate(
                {"name": name, "description": "", "properties": {"ready": ready}}
            )
            .model_dump_json(by_alias=True, exclude_none=True)
            .encode("utf-8")
        )

    def test_ready_status_marks_a_required_app_ready(self):
        manager = make_manager()
        manager.required_apps_status = {"planner": False, "simulator": False}

        manager.on_app_ready_status(
            None,
            FakeMethod("test.planner.status.ready"),
            None,
            self.ready_payload("planner"),
        )

        self.assertTrue(manager.required_apps_status["planner"])
        self.assertFalse(manager.required_apps_status["simulator"])

    def test_status_from_an_unrequired_app_is_ignored(self):
        manager = make_manager()
        manager.required_apps_status = {"planner": False}

        manager.on_app_ready_status(
            None,
            FakeMethod("test.appender.status.ready"),
            None,
            self.ready_payload("appender"),
        )

        self.assertEqual(manager.required_apps_status, {"planner": False})

    def test_not_ready_status_is_recorded(self):
        manager = make_manager()
        manager.required_apps_status = {"planner": True}

        manager.on_app_ready_status(
            None,
            FakeMethod("test.planner.status.ready"),
            None,
            self.ready_payload("planner", ready=False),
        )

        self.assertFalse(manager.required_apps_status["planner"])

    def test_malformed_status_payload_does_not_raise(self):
        """A bad status message must not tear down the manager's IO thread."""
        manager = make_manager()
        manager.required_apps_status = {"planner": False}

        manager.on_app_ready_status(
            None, FakeMethod("test.planner.status.ready"), None, b"not json"
        )

        self.assertFalse(manager.required_apps_status["planner"])


class TestCommandsWhileDisconnected(unittest.TestCase):
    def test_commands_are_queued_rather_than_lost(self):
        manager = make_manager(connected=False)
        manager.init(START, STOP)
        self.assertEqual(manager.channel.published, [])
        self.assertEqual(len(manager._message_queue), 1)


class TestInitializeRetryLoop(unittest.TestCase):
    """
    The manager republished the initialize command on every retry attempt, so a
    run that succeeded immediately still sent init_max_retry commands and each
    application answered with a ready status that many times.
    """

    MAX_RETRY = 5

    def make_manager_for_retry(self, required_apps, ready):
        manager = make_manager()
        manager.required_apps = required_apps
        manager.required_apps_status = {app: ready for app in required_apps}
        manager.init_max_retry = self.MAX_RETRY
        # Keep the wait short; a run where applications never report ready waits
        # this long on every attempt
        manager.init_retry_delay_s = 0.01
        manager.sim_start_time = START
        manager.sim_stop_time = STOP
        return manager

    def initialize_commands(self, manager):
        """Drains scheduled publishes and returns the initialize commands sent."""
        manager.connection.ioloop.run_pending()
        return [key for key in manager.channel.routing_keys() if key.endswith("init")]

    def test_ready_applications_receive_one_initialize_command(self):
        manager = self.make_manager_for_retry(["planner"], ready=True)
        self.assertTrue(manager._initialize_with_retry())
        self.assertEqual(len(self.initialize_commands(manager)), 1)

    def test_no_required_applications_receive_one_initialize_command(self):
        """all([]) is True, so an empty list must not spin through every retry."""
        manager = self.make_manager_for_retry([], ready=True)
        self.assertTrue(manager._initialize_with_retry())
        self.assertEqual(len(self.initialize_commands(manager)), 1)

    def test_unready_applications_exhaust_the_retries(self):
        manager = self.make_manager_for_retry(["planner"], ready=False)
        self.assertFalse(manager._initialize_with_retry())
        self.assertEqual(len(self.initialize_commands(manager)), self.MAX_RETRY)

    def test_application_becoming_ready_mid_wait_stops_the_retries(self):
        """
        A late-arriving ready status must end the retries, not merely shorten one
        wait. This is the case the defect made indistinguishable from success.
        """
        manager = self.make_manager_for_retry(["planner"], ready=False)
        manager.init_retry_delay_s = 5

        def report_ready():
            time.sleep(0.2)
            manager.required_apps_status["planner"] = True

        threading.Thread(target=report_ready, daemon=True).start()
        self.assertTrue(manager._initialize_with_retry())
        self.assertEqual(len(self.initialize_commands(manager)), 1)


class TestRequiredAppsAreReady(unittest.TestCase):
    def test_true_when_every_application_is_ready(self):
        manager = make_manager()
        manager.required_apps = ["planner", "simulator"]
        manager.required_apps_status = {"planner": True, "simulator": True}
        self.assertTrue(manager._required_apps_are_ready())

    def test_false_when_any_application_is_not_ready(self):
        manager = make_manager()
        manager.required_apps = ["planner", "simulator"]
        manager.required_apps_status = {"planner": True, "simulator": False}
        self.assertFalse(manager._required_apps_are_ready())

    def test_true_when_no_applications_are_required(self):
        manager = make_manager()
        manager.required_apps = []
        manager.required_apps_status = {}
        self.assertTrue(manager._required_apps_are_ready())


if __name__ == "__main__":
    unittest.main()
