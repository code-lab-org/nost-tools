import unittest
from datetime import datetime, timedelta, timezone

from nost_tools.observer import (
    MessageObservable,
    MessageObserver,
    Observable,
    Observer,
    PropertyChangeCallback,
    ScenarioTimeIntervalCallback,
    WallclockTimeIntervalCallback,
)
from nost_tools.simulator import Mode, Simulator


# set up test observer
class TestObserver(Observer):
    def __init__(self):
        self.last_source = None
        self.last_property_name = None
        self.last_old_value = None
        self.last_new_value = None

    def on_change(self, source, property_name, old_value, new_value):
        self.last_source = source
        self.last_property_name = property_name
        self.last_old_value = old_value
        self.last_new_value = new_value


class TestObserverMethods(unittest.TestCase):
    def test_one_observable_one_observer(self):
        # configure observable and observer
        observable = Observable()
        observer = TestObserver()
        observable.add_observer(observer)
        # notify observers
        test_property = "test_property"
        test_old_value = "test_old_value"
        test_new_value = "test_new_value"
        observable.notify_observers(test_property, test_old_value, test_new_value)
        # assert values
        self.assertEqual(observer.last_source, observable)
        self.assertEqual(observer.last_property_name, test_property)
        self.assertEqual(observer.last_old_value, test_old_value)
        self.assertEqual(observer.last_new_value, test_new_value)

    def test_one_observable_multi_observer(self):
        # configure observable and observer
        observable = Observable()
        observer_1 = TestObserver()
        observer_2 = TestObserver()
        observable.add_observer(observer_1)
        observable.add_observer(observer_2)
        # notify observers
        test_property = "test_property"
        test_old_value = "test_old_value"
        test_new_value = "test_new_value"
        observable.notify_observers(test_property, test_old_value, test_new_value)
        # assert values
        self.assertEqual(observer_1.last_source, observable)
        self.assertEqual(observer_1.last_property_name, test_property)
        self.assertEqual(observer_1.last_old_value, test_old_value)
        self.assertEqual(observer_1.last_new_value, test_new_value)
        self.assertEqual(observer_2.last_source, observable)
        self.assertEqual(observer_2.last_property_name, test_property)
        self.assertEqual(observer_2.last_old_value, test_old_value)
        self.assertEqual(observer_2.last_new_value, test_new_value)

    def test_multi_observable_one_observer(self):
        # configure observable and observer
        observable_1 = Observable()
        observable_2 = Observable()
        observer = TestObserver()
        observable_1.add_observer(observer)
        observable_2.add_observer(observer)
        # notify observers
        test_property_1 = "test_property_1"
        test_old_value_1 = "test_old_value_1"
        test_new_value_1 = "test_new_value_1"
        observable_1.notify_observers(
            test_property_1, test_old_value_1, test_new_value_1
        )
        # assert values
        self.assertEqual(observer.last_source, observable_1)
        self.assertEqual(observer.last_property_name, test_property_1)
        self.assertEqual(observer.last_old_value, test_old_value_1)
        self.assertEqual(observer.last_new_value, test_new_value_1)
        # notify observers
        test_property_2 = "test_property_2"
        test_old_value_2 = "test_old_value_2"
        test_new_value_2 = "test_new_value_2"
        observable_2.notify_observers(
            test_property_2, test_old_value_2, test_new_value_2
        )
        # assert values
        self.assertEqual(observer.last_source, observable_2)
        self.assertEqual(observer.last_property_name, test_property_2)
        self.assertEqual(observer.last_old_value, test_old_value_2)
        self.assertEqual(observer.last_new_value, test_new_value_2)

    def test_one_observable_no_change(self):
        # configure observable and observer
        observable = Observable()
        observer = TestObserver()
        observable.add_observer(observer)
        # notify observers
        test_property = "test_property"
        test_old_value = "test_value"
        test_new_value = "test_value"
        observable.notify_observers(test_property, test_old_value, test_new_value)
        # assert values
        self.assertIsNone(observer.last_source)
        self.assertIsNone(observer.last_property_name)
        self.assertIsNone(observer.last_old_value)
        self.assertIsNone(observer.last_new_value)


class FakeSimulator:
    """Stands in for a Simulator with a wallclock the test controls."""

    def __init__(self, wallclock_time):
        self.wallclock_time = wallclock_time

    def get_wallclock_time(self):
        return self.wallclock_time


class TestPropertyChangeCallback(unittest.TestCase):
    def test_fires_only_for_the_named_property(self):
        calls = []
        callback = PropertyChangeCallback(
            "mode", lambda source, value: calls.append(value)
        )

        callback.on_change(object(), "mode", "old", "new")
        self.assertEqual(calls, ["new"])

        callback.on_change(object(), "time", "old", "other")
        self.assertEqual(calls, ["new"])

    def test_passes_source_and_new_value(self):
        received = []
        source = object()
        callback = PropertyChangeCallback(
            "mode", lambda src, value: received.append((src, value))
        )
        callback.on_change(source, "mode", "old", "new")
        self.assertEqual(received, [(source, "new")])


class TestScenarioTimeIntervalCallback(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        self.fired = []

    def make(self, interval, time_init=None):
        return ScenarioTimeIntervalCallback(
            lambda source, time: self.fired.append(time), interval, time_init
        )

    def test_fires_at_each_interval(self):
        callback = self.make(timedelta(hours=1))
        callback.on_change(
            Simulator,
            Simulator.PROPERTY_TIME,
            self.start,
            self.start + timedelta(hours=1),
        )
        self.assertEqual(self.fired, [self.start + timedelta(hours=1)])

    def test_catches_up_when_a_step_spans_several_intervals(self):
        """A single large time step must fire once per interval it crossed."""
        callback = self.make(timedelta(hours=1))
        callback.on_change(
            Simulator,
            Simulator.PROPERTY_TIME,
            self.start,
            self.start + timedelta(hours=3),
        )
        self.assertEqual(
            self.fired,
            [
                self.start + timedelta(hours=1),
                self.start + timedelta(hours=2),
                self.start + timedelta(hours=3),
            ],
        )

    def test_first_trigger_defaults_to_one_interval(self):
        callback = self.make(timedelta(hours=6))
        callback.on_change(
            Simulator,
            Simulator.PROPERTY_TIME,
            self.start,
            self.start + timedelta(hours=6),
        )
        self.assertEqual(self.fired, [self.start + timedelta(hours=6)])

    def test_time_init_offsets_the_first_trigger_without_drift(self):
        """
        Regression guard for the drift fixed in 3.0.9: time_init decouples the
        first trigger from the repeating interval, so a daily callback set to fire
        at 23:55 keeps firing at 23:55 rather than sliding each day.
        """
        callback = self.make(
            timedelta(days=1), time_init=timedelta(hours=23, minutes=55)
        )
        callback.on_change(
            Simulator,
            Simulator.PROPERTY_TIME,
            self.start,
            self.start + timedelta(days=3),
        )
        expected = [
            self.start + timedelta(hours=23, minutes=55),
            self.start + timedelta(days=1, hours=23, minutes=55),
            self.start + timedelta(days=2, hours=23, minutes=55),
        ]
        self.assertEqual(self.fired, expected)

    def test_ignores_other_properties(self):
        callback = self.make(timedelta(hours=1))
        callback.on_change(
            Simulator, Simulator.PROPERTY_MODE, Mode.INITIALIZED, Mode.EXECUTING
        )
        self.assertEqual(self.fired, [])


class TestWallclockTimeIntervalCallback(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2020, 1, 1, tzinfo=timezone.utc)
        self.simulator = FakeSimulator(self.now)
        self.fired = []

    def make(self, interval, time_init=None):
        return WallclockTimeIntervalCallback(
            self.simulator, lambda time: self.fired.append(time), interval, time_init
        )

    def test_fires_once_the_wallclock_passes_the_interval(self):
        callback = self.make(timedelta(seconds=10))
        # First time change establishes the next trigger, one interval ahead
        callback.on_change(self.simulator, Simulator.PROPERTY_TIME, None, None)
        self.assertEqual(self.fired, [])

        self.simulator.wallclock_time = self.now + timedelta(seconds=10)
        callback.on_change(self.simulator, Simulator.PROPERTY_TIME, None, None)
        self.assertEqual(self.fired, [self.now + timedelta(seconds=10)])

    def test_catches_up_across_several_intervals(self):
        callback = self.make(timedelta(seconds=10))
        callback.on_change(self.simulator, Simulator.PROPERTY_TIME, None, None)

        self.simulator.wallclock_time = self.now + timedelta(seconds=30)
        callback.on_change(self.simulator, Simulator.PROPERTY_TIME, None, None)
        self.assertEqual(
            self.fired,
            [
                self.now + timedelta(seconds=10),
                self.now + timedelta(seconds=20),
                self.now + timedelta(seconds=30),
            ],
        )

    def test_initialized_mode_seeds_the_next_trigger_from_time_init(self):
        time_init = self.now + timedelta(seconds=5)
        callback = self.make(timedelta(seconds=10), time_init=time_init)
        callback.on_change(
            self.simulator, Simulator.PROPERTY_MODE, Mode.INITIALIZING, Mode.INITIALIZED
        )
        self.assertEqual(callback._next_time, time_init)

    def test_resuming_resets_the_next_trigger(self):
        """
        After a freeze the wallclock has advanced, so the next trigger is rebased
        rather than firing repeatedly to catch up on time spent paused.
        """
        callback = self.make(timedelta(seconds=10))
        callback.on_change(self.simulator, Simulator.PROPERTY_TIME, None, None)

        self.simulator.wallclock_time = self.now + timedelta(hours=1)
        callback.on_change(
            self.simulator, Simulator.PROPERTY_MODE, Mode.RESUMING, Mode.EXECUTING
        )

        self.assertEqual(callback._next_time, self.now + timedelta(hours=1, seconds=10))
        self.assertEqual(self.fired, [])


class RecordingMessageObserver(MessageObserver):
    def __init__(self):
        self.messages = []

    def on_message(self, ch, method, properties, body):
        self.messages.append(body)


class TestMessageObservable(unittest.TestCase):
    def test_notifies_every_registered_observer(self):
        observable = MessageObservable()
        first, second = RecordingMessageObserver(), RecordingMessageObserver()
        observable.add_message_observer(first)
        observable.add_message_observer(second)

        observable.notify_message_observers(None, None, None, b"payload")

        self.assertEqual(first.messages, [b"payload"])
        self.assertEqual(second.messages, [b"payload"])

    def test_removed_observer_stops_receiving(self):
        observable = MessageObservable()
        observer = RecordingMessageObserver()
        observable.add_message_observer(observer)
        observable.remove_message_observer(observer)

        observable.notify_message_observers(None, None, None, b"payload")

        self.assertEqual(observer.messages, [])
