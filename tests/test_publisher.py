"""
Tests for the interval publishers that emit time status ("heartbeat") messages.
"""

import unittest
from datetime import datetime, timedelta, timezone

from nost_tools.publisher import (
    ScenarioTimeIntervalPublisher,
    WallclockTimeIntervalPublisher,
)
from nost_tools.simulator import Mode, Simulator

START = datetime(2020, 1, 1, tzinfo=timezone.utc)


class FakeSimulator:
    """Stands in for a Simulator with time values the test controls."""

    def __init__(self, init_time=START, time_step=timedelta(seconds=1)):
        self.init_time = init_time
        self.time_step = time_step
        self.wallclock_time = START

    def get_init_time(self):
        return self.init_time

    def get_time_step(self):
        return self.time_step

    def get_wallclock_time(self):
        return self.wallclock_time


class FakeApp:
    def __init__(self, simulator):
        self.simulator = simulator


class RecordingScenarioPublisher(ScenarioTimeIntervalPublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.published = 0

    def publish_message(self):
        self.published += 1


class RecordingWallclockPublisher(WallclockTimeIntervalPublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.published = 0

    def publish_message(self):
        self.published += 1


class TestScenarioTimeIntervalPublisher(unittest.TestCase):
    def setUp(self):
        self.simulator = FakeSimulator()
        self.app = FakeApp(self.simulator)

    def initialize(self, publisher):
        publisher.on_change(
            Simulator, Simulator.PROPERTY_MODE, Mode.INITIALIZING, Mode.INITIALIZED
        )

    def test_publishes_once_per_step_interval(self):
        publisher = RecordingScenarioPublisher(self.app, timedelta(hours=1))
        self.initialize(publisher)
        publisher.on_change(
            Simulator, Simulator.PROPERTY_TIME, START, START + timedelta(hours=1)
        )
        # Fires for the init time and the one-hour mark
        self.assertEqual(publisher.published, 2)

    def test_catches_up_across_several_intervals(self):
        publisher = RecordingScenarioPublisher(self.app, timedelta(hours=1))
        self.initialize(publisher)
        publisher.on_change(
            Simulator, Simulator.PROPERTY_TIME, START, START + timedelta(hours=3)
        )
        self.assertEqual(publisher.published, 4)

    def test_falls_back_to_the_simulator_time_step(self):
        """With no explicit step, the publisher follows the simulator's."""
        publisher = RecordingScenarioPublisher(self.app, None)
        self.initialize(publisher)
        publisher.on_change(
            Simulator, Simulator.PROPERTY_TIME, START, START + timedelta(seconds=3)
        )
        self.assertEqual(publisher.published, 4)

    def test_time_status_init_overrides_the_first_publish_time(self):
        publisher = RecordingScenarioPublisher(
            self.app, timedelta(hours=1), time_status_init=START + timedelta(hours=2)
        )
        self.initialize(publisher)
        publisher.on_change(
            Simulator, Simulator.PROPERTY_TIME, START, START + timedelta(hours=1)
        )
        self.assertEqual(publisher.published, 0)

        publisher.on_change(
            Simulator,
            Simulator.PROPERTY_TIME,
            START + timedelta(hours=1),
            START + timedelta(hours=2),
        )
        self.assertEqual(publisher.published, 1)


class TestWallclockTimeIntervalPublisher(unittest.TestCase):
    def setUp(self):
        self.simulator = FakeSimulator()
        self.app = FakeApp(self.simulator)

    def initialize(self, publisher):
        """
        Seeds the first publish time, as the simulator does on reaching INITIALIZED.

        Unlike WallclockTimeIntervalCallback in observer.py, this publisher has no
        fallback when a time change arrives before initialization, so the order
        here mirrors the real notification sequence.
        """
        publisher.on_change(
            Simulator, Simulator.PROPERTY_MODE, Mode.INITIALIZING, Mode.INITIALIZED
        )

    def test_publishes_once_the_wallclock_passes_the_interval(self):
        publisher = RecordingWallclockPublisher(self.app, timedelta(seconds=10))
        self.initialize(publisher)

        publisher.on_change(Simulator, Simulator.PROPERTY_TIME, None, None)
        self.assertEqual(publisher.published, 1)

        self.simulator.wallclock_time = START + timedelta(seconds=10)
        publisher.on_change(Simulator, Simulator.PROPERTY_TIME, None, None)
        self.assertEqual(publisher.published, 2)

    def test_catches_up_across_several_intervals(self):
        publisher = RecordingWallclockPublisher(self.app, timedelta(seconds=10))
        self.initialize(publisher)
        publisher.on_change(Simulator, Simulator.PROPERTY_TIME, None, None)

        self.simulator.wallclock_time = START + timedelta(seconds=30)
        publisher.on_change(Simulator, Simulator.PROPERTY_TIME, None, None)
        self.assertEqual(publisher.published, 4)

    def test_resuming_rebases_the_next_publish_time(self):
        """After a freeze the wallclock has advanced, so the schedule is rebased
        rather than firing repeatedly to catch up on time spent paused."""
        publisher = RecordingWallclockPublisher(self.app, timedelta(seconds=10))
        self.initialize(publisher)

        self.simulator.wallclock_time = START + timedelta(hours=1)
        publisher.on_change(
            Simulator, Simulator.PROPERTY_MODE, Mode.RESUMING, Mode.EXECUTING
        )
        publisher.on_change(Simulator, Simulator.PROPERTY_TIME, None, None)

        self.assertEqual(publisher.published, 0)


if __name__ == "__main__":
    unittest.main()
