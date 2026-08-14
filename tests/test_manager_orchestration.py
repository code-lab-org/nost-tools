"""
Tests for the manager's request handling, freeze/resume coordination, and the
sequencing in its test plan.

The manager waits on wallclock time and mode transitions that a real simulator
drives from another thread. These tests substitute a simulator whose clock the
test controls, so sequencing can be asserted without waiting out a scenario.
"""

import json
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from nost_tools.manager import Manager
from nost_tools.schemas import FreezeRequest, ResumeRequest, UpdateRequest
from nost_tools.simulator import Mode

from .fakes import FakeSimulator, wire_broker

START = datetime(2020, 1, 1, tzinfo=timezone.utc)
STOP = datetime(2020, 1, 2, tzinfo=timezone.utc)


class FakeMethod:
    """Stands in for pika's Basic.Deliver frame."""

    def __init__(self, routing_key="test.app.request"):
        self.routing_key = routing_key


def make_manager(mode=Mode.EXECUTING, scenario_time=START):
    """Builds a manager wired to broker doubles and a controllable simulator."""
    manager = wire_broker(Manager("test_manager", setup_signal_handlers=False))
    manager.simulator = FakeSimulator(mode=mode, scenario_time=scenario_time)
    manager.required_apps = []
    manager.required_apps_status = {}
    # Keep any wait the manager performs short
    manager.init_retry_delay_s = 0.01
    manager.init_max_retry = 1
    manager.command_lead = timedelta(seconds=0)
    return manager


def published(manager, suffix):
    """Drains scheduled publishes and returns bodies sent to a topic suffix."""
    manager.connection.ioloop.run_pending()
    return [
        json.loads(body)
        for key, body in zip(manager.channel.routing_keys(), manager.channel.bodies())
        if key.endswith(suffix)
    ]


def freeze_request(sim_freeze_time=None, freeze_duration=None, resume_time=None):
    params = {
        "requestingApp": "planner",
        "simFreezeTime": sim_freeze_time or START,
        "freezeTime": sim_freeze_time or START,
    }
    if freeze_duration is not None:
        params["freezeDuration"] = freeze_duration
    if resume_time is not None:
        params["resumeTime"] = resume_time
    return (
        FreezeRequest.model_validate({"taskingParameters": params})
        .model_dump_json(by_alias=True)
        .encode("utf-8")
    )


def resume_request(sim_resume_time=None, tolerance=None):
    params = {"requestingApp": "planner"}
    if sim_resume_time is not None:
        params["simResumeTime"] = sim_resume_time
    if tolerance is not None:
        params["tolerance"] = tolerance
    return (
        ResumeRequest.model_validate({"taskingParameters": params})
        .model_dump_json(by_alias=True)
        .encode("utf-8")
    )


def update_request(time_scale_factor, sim_update_time=None):
    params = {"requestingApp": "planner", "timeScalingFactor": time_scale_factor}
    if sim_update_time is not None:
        params["simUpdateTime"] = sim_update_time
    return (
        UpdateRequest.model_validate({"taskingParameters": params})
        .model_dump_json(by_alias=True)
        .encode("utf-8")
    )


class TestFreezeCommand(unittest.TestCase):
    """
    freeze() blocks: it pauses the simulator, waits for the PAUSED mode, then
    holds until the freeze elapses or something resumes. These tests run it on a
    thread and release it, rather than waiting out a real freeze.
    """

    def run_freeze(self, manager, **kwargs):
        """Starts freeze() on a thread and returns it once the pause has landed."""
        thread = threading.Thread(
            target=manager.freeze, kwargs=kwargs, daemon=True
        )
        thread.start()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and manager.simulator.pause_calls == 0:
            time.sleep(0.01)
        return thread

    def release(self, manager, thread):
        """Ends an indefinite freeze so the thread can finish."""
        manager.simulator.mode = Mode.EXECUTING
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive(), "freeze() did not return")

    def test_indefinite_freeze_publishes_without_a_duration(self):
        manager = make_manager()
        thread = self.run_freeze(manager, sim_freeze_time=START)

        bodies = published(manager, "freeze")
        self.assertEqual(len(bodies), 1)
        # The key is present with a null value rather than omitted, since the
        # schema field defaults to None and the dump does not exclude it
        self.assertIsNone(bodies[0]["taskingParameters"]["freezeDuration"])
        self.assertEqual(
            bodies[0]["taskingParameters"]["simFreezeTime"], "2020-01-01T00:00:00Z"
        )
        self.release(manager, thread)

    def test_freeze_pauses_the_simulator(self):
        manager = make_manager()
        thread = self.run_freeze(manager, sim_freeze_time=START)
        self.assertEqual(manager.simulator.pause_calls, 1)
        self.release(manager, thread)

    def test_indefinite_freeze_returns_once_execution_resumes(self):
        manager = make_manager()
        thread = self.run_freeze(manager, sim_freeze_time=START)
        self.release(manager, thread)

class TestFreezeArgumentRequirements(unittest.TestCase):
    """
    Documents current behaviour rather than endorsing it.

    Three parameters are optional in the signature, but only one combination
    works. The signature, the docstring, and the implementation disagree:

      freeze()                                 -> ValidationError
      freeze(freeze_duration=D)                -> TypeError
      freeze(freeze_duration=D, sim_freeze_time=T) -> TypeError
      freeze(sim_freeze_time=T)                -> indefinite freeze, works

    These tests pin the failures so a fix has to change them deliberately.
    """

    def call_freeze(self, manager, **kwargs):
        """Runs freeze() on a thread and returns any exception it raised."""
        raised = []

        def go():
            try:
                manager.freeze(**kwargs)
            except Exception as e:  # noqa: BLE001 - the failure is the subject
                raised.append(e)

        thread = threading.Thread(target=go, daemon=True)
        thread.start()
        thread.join(timeout=5)
        return raised[0] if raised else None

    def test_no_arguments_is_rejected(self):
        """
        The docstring describes sim_freeze_time=None as "freezes immediately",
        but the command schema requires the field.
        """
        manager = make_manager()
        error = self.call_freeze(manager)
        self.assertIsNotNone(error, "expected freeze() with no arguments to raise")
        self.assertIn("simFreezeTime", str(error))

    def test_a_duration_without_a_resume_time_is_rejected(self):
        """
        A timed freeze subtracts resume_time from the wallclock, so leaving it at
        its documented default fails inside the wait loop rather than at the call
        site. resume_time is not mentioned in the docstring at all.
        """
        manager = make_manager()
        error = self.call_freeze(
            manager, freeze_duration=timedelta(minutes=5), sim_freeze_time=START
        )
        self.assertIsInstance(error, TypeError)
        self.assertIn("NoneType", str(error))


class TestResumeCommand(unittest.TestCase):
    def test_resume_publishes_and_resumes_the_simulator(self):
        manager = make_manager(mode=Mode.PAUSED)
        manager.resume()

        self.assertEqual(len(published(manager, "resume")), 1)
        self.assertEqual(manager.simulator.resume_calls, 1)


class TestFreezeRequests(unittest.TestCase):
    def wait_for_publish(self, manager, suffix, timeout=5):
        """Requests are handled on a thread, so wait for the command to appear."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if published(manager, suffix):
                return True
            time.sleep(0.01)
        return False

    def test_freeze_request_publishes_a_freeze_command(self):
        manager = make_manager()
        manager.on_freeze_request(None, FakeMethod(), None, freeze_request())
        self.assertTrue(self.wait_for_publish(manager, "freeze"))

    def test_malformed_freeze_request_does_not_raise(self):
        """A bad request must not tear down the manager's IO thread."""
        manager = make_manager()
        manager.on_freeze_request(None, FakeMethod(), None, b"not json")
        self.assertEqual(published(manager, "freeze"), [])


class TestResumeRequests(unittest.TestCase):
    def test_resume_within_tolerance_resumes(self):
        manager = make_manager(mode=Mode.PAUSED, scenario_time=START)
        manager._handle_resume_request(
            START + timedelta(seconds=5), timedelta(seconds=30)
        )
        self.assertEqual(manager.simulator.resume_calls, 1)

    def test_resume_outside_tolerance_is_ignored(self):
        """
        A request naming a scenario time far from the present is held rather than
        acted on, so a stale request does not resume at the wrong moment.
        """
        manager = make_manager(mode=Mode.PAUSED, scenario_time=START)
        manager._handle_resume_request(
            START + timedelta(hours=5), timedelta(seconds=30)
        )
        self.assertEqual(manager.simulator.resume_calls, 0)

    def test_malformed_resume_request_does_not_raise(self):
        manager = make_manager(mode=Mode.PAUSED)
        manager.on_resume_request(None, FakeMethod(), None, b"not json")
        self.assertEqual(manager.simulator.resume_calls, 0)


class TestUpdateRequests(unittest.TestCase):
    def test_update_request_applies_once_executing(self):
        manager = make_manager(mode=Mode.EXECUTING)
        manager.on_update_request(
            None, FakeMethod(), None, update_request(30.0, START + timedelta(hours=1))
        )

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if manager.simulator.set_time_scale_factor_calls:
                break
            time.sleep(0.01)

        self.assertEqual(
            manager.simulator.set_time_scale_factor_calls[0][0], 30.0
        )

    def test_malformed_update_request_does_not_raise(self):
        manager = make_manager()
        manager.on_update_request(None, FakeMethod(), None, b"not json")
        self.assertEqual(manager.simulator.set_time_scale_factor_calls, [])


class TestTimeStatusHandling(unittest.TestCase):
    def test_time_status_from_an_application_is_recorded(self):
        """Latency logging must not raise on a well-formed status."""
        manager = make_manager()
        payload = json.dumps(
            {
                "name": "planner",
                "properties": {
                    "simTime": START.isoformat(),
                    "time": START.isoformat(),
                },
            }
        ).encode("utf-8")
        manager.on_app_time_status(
            None, FakeMethod("test.planner.status.time"), None, payload
        )

    def test_malformed_time_status_does_not_raise(self):
        manager = make_manager()
        manager.on_app_time_status(
            None, FakeMethod("test.planner.status.time"), None, b"not json"
        )


class TestStartCommand(unittest.TestCase):
    def test_start_publishes_the_scenario_window_and_scale(self):
        manager = make_manager()
        manager.simulator.execute = lambda **kwargs: None

        manager.start(
            START, STOP, start_time=START, time_step=timedelta(seconds=1),
            time_scale_factor=60.0,
        )

        bodies = published(manager, "start")
        self.assertEqual(len(bodies), 1)
        params = bodies[0]["taskingParameters"]
        self.assertEqual(params["simStartTime"], "2020-01-01T00:00:00Z")
        self.assertEqual(params["simStopTime"], "2020-01-02T00:00:00Z")
        self.assertEqual(params["timeScalingFactor"], 60.0)

    def test_start_executes_the_simulator(self):
        manager = make_manager()
        executed = []
        manager.simulator.execute = lambda **kwargs: executed.append(kwargs)

        manager.start(
            START, STOP, start_time=START, time_step=timedelta(seconds=1),
            time_scale_factor=60.0,
        )

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not executed:
            time.sleep(0.01)
        self.assertEqual(len(executed), 1)
        self.assertEqual(executed[0]["init_time"], START)
        self.assertEqual(executed[0]["duration"], STOP - START)


class TestStopCommand(unittest.TestCase):
    def test_stop_sets_the_end_time_while_executing(self):
        manager = make_manager(mode=Mode.EXECUTING)
        manager.stop(STOP)

        self.assertEqual(len(published(manager, "stop")), 1)
        self.assertEqual(manager.simulator.set_end_time_calls, [STOP])

    def test_stop_skips_the_end_time_when_not_executing(self):
        """
        set_end_time requires EXECUTING, so the manager checks the mode first
        rather than letting it raise.
        """
        manager = make_manager(mode=Mode.UNDEFINED)
        manager.stop(STOP)

        self.assertEqual(len(published(manager, "stop")), 1)
        self.assertEqual(manager.simulator.set_end_time_calls, [])


class TestTestPlanSequencing(unittest.TestCase):
    """
    Drives _execute_test_plan_impl end to end with a controlled clock.

    Subscription setup and the time status publisher are stubbed: they exercise
    broker mechanics covered elsewhere, and they are not what this asserts.
    """

    def make_plan_manager(self, yaml_file=None, parameters=None):
        manager = make_manager(mode=Mode.EXECUTING)
        # The stop wait ends as soon as the scenario end time maps to now
        manager.simulator.end_time = manager.simulator.get_time()

        config = MagicMock()
        config.rc.yaml_file = yaml_file
        if parameters is not None:
            setattr(
                config.rc.simulation_configuration.execution_parameters,
                manager.app_name,
                parameters,
            )
        manager.config = config

        manager.add_message_callback = lambda *args, **kwargs: None
        manager._create_time_status_publisher = lambda *args, **kwargs: None
        manager.simulator.execute = lambda **kwargs: None
        return manager

    def test_commands_are_published_in_order(self):
        manager = self.make_plan_manager()

        manager._execute_test_plan_impl(
            sim_start_time=START,
            sim_stop_time=STOP,
            start_time=START,
            time_scale_factor=60.0,
            required_apps=[],
        )

        manager.connection.ioloop.run_pending()
        sequence = [
            key.rsplit(".", 1)[-1]
            for key in manager.channel.routing_keys()
            if key.rsplit(".", 1)[-1] in ("init", "start", "stop")
        ]
        self.assertEqual(sequence, ["init", "start", "stop"])

    def test_arguments_are_used_when_no_yaml_file_is_configured(self):
        manager = self.make_plan_manager()

        # The retry settings must be passed here: _execute_test_plan_impl assigns
        # them from its own arguments, discarding anything set beforehand
        manager._execute_test_plan_impl(
            sim_start_time=START,
            sim_stop_time=STOP,
            start_time=START,
            time_scale_factor=42.0,
            required_apps=["planner"],
            init_retry_delay_s=0.01,
            init_max_retry=1,
        )

        self.assertEqual(manager.sim_start_time, START)
        self.assertEqual(manager.sim_stop_time, STOP)
        self.assertEqual(manager.time_scale_factor, 42.0)
        self.assertEqual(manager.required_apps, ["planner"])

    def test_yaml_parameters_take_precedence_over_arguments(self):
        """
        With a YAML file configured the arguments are ignored entirely, which is
        why the maintained examples call execute_test_plan() with none.
        """
        parameters = SimpleNamespace(
            sim_start_time=START,
            sim_stop_time=STOP,
            start_time=START,
            time_step=timedelta(seconds=1),
            time_scale_factor=99.0,
            time_status_step=timedelta(seconds=10),
            time_status_init=START,
            command_lead=timedelta(seconds=0),
            required_apps=["planner", "test_manager"],
            init_retry_delay_s=0.01,
            init_max_retry=1,
        )
        manager = self.make_plan_manager(
            yaml_file="config.yaml", parameters=parameters
        )

        manager._execute_test_plan_impl(
            sim_start_time=None,
            sim_stop_time=None,
            time_scale_factor=1.0,
            required_apps=["ignored"],
        )

        self.assertEqual(manager.time_scale_factor, 99.0)
        # The manager excludes itself from the applications it waits on
        self.assertEqual(manager.required_apps, ["planner"])

    def test_required_apps_status_is_seeded_from_the_app_list(self):
        manager = self.make_plan_manager()

        manager._execute_test_plan_impl(
            sim_start_time=START,
            sim_stop_time=STOP,
            start_time=START,
            required_apps=[],
        )

        self.assertEqual(manager.required_apps_status, {})


class TestSleepWithHeartbeat(unittest.TestCase):
    def test_returns_immediately_for_a_non_positive_duration(self):
        manager = make_manager()
        started = time.monotonic()
        manager._sleep_with_heartbeat(0)
        manager._sleep_with_heartbeat(-5)
        self.assertLess(time.monotonic() - started, 0.5)

    def test_sleeps_for_the_requested_duration(self):
        manager = make_manager()
        started = time.monotonic()
        manager._sleep_with_heartbeat(0.2)
        self.assertGreaterEqual(time.monotonic() - started, 0.15)


if __name__ == "__main__":
    unittest.main()
