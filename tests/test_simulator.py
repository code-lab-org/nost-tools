import unittest
from datetime import datetime, timedelta, timezone
import threading
import time

from nost_tools.observer import RecordingObserver
from nost_tools.entity import Entity
from nost_tools.simulator import Mode, Simulator


class NullEntity(Entity):
    pass

class TestSimulatorMethods(unittest.TestCase):
    def test_simulator_add_remove_entity(self):
        simulator = Simulator()
        entity_1 = NullEntity("test_1")
        entity_2 = NullEntity("test_2")
        simulator.add_entity(entity_1)
        self.assertIn(entity_1, simulator.get_entities())
        simulator.add_entity(entity_2)
        self.assertIn(entity_2, simulator.get_entities())
        simulator.remove_entity(entity_2)
        self.assertNotIn(entity_2, simulator.get_entities())
        self.assertIn(entity_1, simulator.get_entities())
        simulator.remove_entity(entity_1)
        self.assertNotIn(entity_1, simulator.get_entities())

    def test_simulator_get_entities(self):
        simulator = Simulator()
        entity_1 = NullEntity("test_1")
        entity_2 = NullEntity("test_2")
        simulator.add_entity(entity_1)
        simulator.add_entity(entity_2)
        self.assertIn(entity_1, simulator.get_entities())
        self.assertIn(entity_2, simulator.get_entities())

    def test_simulator_get_entities_by_name(self):
        simulator = Simulator()
        entity_1 = NullEntity("test_1")
        entity_2 = NullEntity("test_2")
        simulator.add_entity(entity_1)
        simulator.add_entity(entity_2)
        self.assertIn(entity_1, simulator.get_entities_by_name("test_1"))
        self.assertNotIn(entity_2, simulator.get_entities_by_name("test_1"))

    def test_simulator_get_entities_by_type(self):
        simulator = Simulator()
        entity_1 = NullEntity("test_1")
        entity_2 = Entity("test_2")
        simulator.add_entity(entity_1)
        simulator.add_entity(entity_2)
        self.assertIn(entity_1, simulator.get_entities_by_type(NullEntity))
        self.assertNotIn(entity_2, simulator.get_entities_by_type(NullEntity))
        self.assertIn(entity_1, simulator.get_entities_by_type(Entity))
        self.assertIn(entity_2, simulator.get_entities_by_type(Entity))

    def test_simulator_get_entities_shallow_copy(self):
        simulator = Simulator()
        entity_1 = NullEntity("test_1")
        entity_2 = NullEntity("test_2")
        simulator.add_entity(entity_1)
        self.assertIn(entity_1, simulator.get_entities())
        simulator.get_entities().append(entity_2)
        self.assertNotIn(entity_2, simulator.get_entities())

    def test_simulator_bad_remove_entity(self):
        simulator = Simulator()
        entity_1 = NullEntity("test_1")
        entity_2 = NullEntity("test_2")
        simulator.add_entity(entity_1)
        self.assertIn(entity_1, simulator.get_entities())
        self.assertIsNone(simulator.remove_entity(entity_2))
        self.assertNotIn(entity_2, simulator.get_entities())

    def test_simulator_initialize_time(self):
        simulator = Simulator()
        entity = Entity("test")
        simulator.add_entity(entity)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        simulator.initialize(init_time)
        self.assertEqual(simulator.get_time(), init_time)
        self.assertEqual(entity.get_time(), init_time)

    def test_simulator_initialize_mode(self):
        simulator = Simulator()
        entity_1 = Entity("test_1")
        entity_2 = Entity("test_2")
        simulator.add_entity(entity_1)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(simulator.get_mode(), Mode.UNDEFINED)
        simulator.initialize(init_time)
        self.assertEqual(simulator.get_mode(), Mode.INITIALIZED)
        simulator.add_entity(entity_2)
        self.assertEqual(simulator.get_mode(), Mode.UNDEFINED)
        simulator.initialize(init_time)
        self.assertEqual(simulator.get_mode(), Mode.INITIALIZED)
        simulator.remove_entity(entity_2)
        self.assertEqual(simulator.get_mode(), Mode.UNDEFINED)

    def test_simulator_execute_time_as_fast_as_possible(self):
        simulator = Simulator()
        recorder = RecordingObserver("time")
        simulator.add_observer(recorder)
        entity = Entity("test")
        simulator.add_entity(entity)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        duration = timedelta(seconds=5)
        time_step = timedelta(seconds=1)
        simulator.execute(init_time, duration, time_step, time_scale_factor=None)
        self.assertEqual(entity.get_time(), init_time + duration)
        self.assertEqual(simulator.get_time(), init_time + duration)
        self.assertEqual(recorder.changes[-1]["new_value"], init_time + duration)
        self.assertEqual(entity.get_time(), init_time + duration)

    def test_simulator_execute_time_scale_100(self):
        simulator = Simulator()
        recorder = RecordingObserver("time")
        simulator.add_observer(recorder)
        entity = Entity("test")
        simulator.add_entity(entity)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        duration = timedelta(seconds=5)
        time_step = timedelta(seconds=1)
        simulator.execute(init_time, duration, time_step, time_scale_factor=100)
        self.assertEqual(entity.get_time(), init_time + duration)
        self.assertEqual(simulator.get_time(), init_time + duration)
        self.assertEqual(recorder.changes[-1]["new_value"], init_time + duration)
        self.assertEqual(entity.get_time(), init_time + duration)

    def test_simulator_execute_time_partial_final_time_step(self):
        simulator = Simulator()
        recorder = RecordingObserver("time")
        simulator.add_observer(recorder)
        entity = Entity("test")
        simulator.add_entity(entity)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        duration = timedelta(seconds=5)
        time_step = timedelta(seconds=2)
        simulator.execute(init_time, duration, time_step, time_scale_factor=None)
        self.assertEqual(simulator.get_time(), init_time + duration)
        self.assertEqual(recorder.changes[-1]["new_value"], init_time + duration)
        self.assertEqual(entity.get_time(), init_time + duration)

    def test_simulator_execute_wait_wallclock_epoch(self):
        simulator = Simulator()
        recorder = RecordingObserver("mode", True)
        simulator.add_observer(recorder)
        entity = Entity("test")
        simulator.add_entity(entity)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        t_delay = timedelta(seconds=1)
        t_wallclock = datetime.now(tz=timezone.utc) + t_delay
        duration = timedelta(seconds=0)
        time_step = timedelta(seconds=1)
        simulator.execute(
            init_time,
            duration,
            time_step,
            wallclock_epoch=t_wallclock,
            time_scale_factor=None,
        )
        self.assertAlmostEqual(
            (
                next(change for change in recorder.changes if change["new_value"] == Mode.EXECUTING)["time"]
                - next(change for change in recorder.changes if change["new_value"] == Mode.INITIALIZING)["time"]
            ).total_seconds(),
            t_delay.total_seconds(),
            1,
        )

    def test_simulator_execute_mode_checks(self):
        simulator = Simulator()
        entity = Entity("test")
        simulator.add_entity(entity)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        with self.assertRaises(RuntimeError):
            simulator.terminate()
        # start execution in background thread
        threading.Thread(
            target=simulator.execute,
            kwargs={
                "init_time": init_time,
                "duration": timedelta(hours=1),
                "time_step": timedelta(seconds=1),
                "time_scale_factor": 100,
            },
        ).start()
        # wait for execution to start
        while simulator.get_mode() != Mode.EXECUTING:
            time.sleep(0.1)
        with self.assertRaises(RuntimeError):
            simulator.add_entity(NullEntity())
        with self.assertRaises(RuntimeError):
            simulator.remove_entity(entity)
        with self.assertRaises(RuntimeError):
            simulator.initialize(init_time)
        with self.assertRaises(RuntimeError):
            simulator.set_wallclock_offset(timedelta(seconds=1))
        with self.assertRaises(RuntimeError):
            simulator.execute(init_time, timedelta(minutes=1), timedelta(seconds=1))
        simulator.terminate()
        # wait for execution to terminate
        while simulator.get_mode() != Mode.TERMINATED:
            time.sleep(0.1)

    def test_simulator_execute_change_time_step(self):
        simulator = Simulator()
        recorder = RecordingObserver("time")
        simulator.add_observer(recorder)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        new_time_step = timedelta(seconds=2)
        with self.assertRaises(RuntimeError):
            simulator.set_time_step(new_time_step)
        # start execution in background thread
        threading.Thread(
            target=simulator.execute,
            kwargs={
                "init_time": init_time,
                "duration": timedelta(hours=1),
                "time_step": timedelta(seconds=1),
                "time_scale_factor": 100,
            },
        ).start()
        # wait for execution to start
        while simulator.get_mode() != Mode.EXECUTING:
            time.sleep(0.1)
        simulator.set_time_step(new_time_step)
        # wait for time step to change
        while simulator.get_time_step() != new_time_step:
            time.sleep(0.1)
        simulator.terminate()
        # wait for execution to terminate
        while simulator.get_mode() != Mode.TERMINATED:
            time.sleep(0.1)
        self.assertEqual(
            recorder.changes[-2]["new_value"] - recorder.changes[-3]["new_value"], 
            new_time_step
        )

    def test_simulator_execute_change_duration(self):
        simulator = Simulator()
        recorder = RecordingObserver("time")
        simulator.add_observer(recorder)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        new_duration = timedelta(seconds=20)
        with self.assertRaises(RuntimeError):
            simulator.set_duration(new_duration)
        # start execution in background thread
        threading.Thread(
            target=simulator.execute,
            kwargs={
                "init_time": init_time,
                "duration": timedelta(hours=1),
                "time_step": timedelta(seconds=1),
                "time_scale_factor": 100,
            },
        ).start()
        # wait for execution to start
        while simulator.get_mode() != Mode.EXECUTING:
            time.sleep(0.1)
        simulator.set_duration(new_duration)
        # wait for execution to terminate
        while simulator.get_mode() != Mode.TERMINATED:
            time.sleep(0.1)
        self.assertEqual(simulator.get_time(), init_time + new_duration)
        self.assertEqual(recorder.changes[-1]["new_value"], init_time + new_duration)

    def test_simulator_execute_change_time_scale_factor(self):
        simulator = Simulator()
        recorder = RecordingObserver("time", True)
        simulator.add_observer(recorder)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        time_step = timedelta(seconds=1)
        new_time_scale_factor = 50
        with self.assertRaises(RuntimeError):
            simulator.set_time_scale_factor(new_time_scale_factor)
        # start execution in background thread
        threading.Thread(
            target=simulator.execute,
            kwargs={
                "init_time": init_time,
                "duration": timedelta(hours=1),
                "time_step": time_step,
                "time_scale_factor": 100,
            },
        ).start()
        # wait for execution to start
        while simulator.get_mode() != Mode.EXECUTING:
            time.sleep(0.1)
        simulator.set_time_scale_factor(new_time_scale_factor)
        # wait for time scale factor to change
        while simulator.get_time_scale_factor() != new_time_scale_factor:
            time.sleep(0.1)
        simulator.terminate()
        # wait for execution to terminate
        while simulator.get_mode() != Mode.TERMINATED:
            time.sleep(0.1)
        self.assertAlmostEqual(
            (recorder.changes[-2]["time"] - recorder.changes[-3]["time"]).total_seconds(),
            (time_step / new_time_scale_factor).total_seconds(),
            1,
        )
