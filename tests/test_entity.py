import unittest
from datetime import datetime, timedelta, timezone

from nost_tools.entity import Entity
from nost_tools.observer import Observer

class TestObserver(Observer):
    changes_observed = []
    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ) -> None:
        self.changes_observed.append({
            "source": source,
            "property_name": property_name,
            "old_value": old_value,
            "new_value": new_value
        })


class TestEntityMethods(unittest.TestCase):
    def test_default_entity_properties(self):
        entity = Entity("test")
        self.assertEqual(entity.name, "test")

    def test_default_entity_initialize(self):
        entity = Entity("test")
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        time_step = timedelta(seconds=1)
        entity.initialize(init_time)
        self.assertEqual(entity.get_time(), init_time)

    def test_default_entity_tick(self):
        entity = Entity("test")
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        time_step = timedelta(seconds=1)
        entity.initialize(init_time)
        entity.tick(time_step)
        self.assertEqual(entity.get_time(), init_time)

    def test_default_entity_tock(self):
        entity = Entity("test")
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        time_step = timedelta(seconds=1)
        entity.initialize(init_time)
        entity.tick(time_step)
        entity.tock()
        self.assertEqual(entity.get_time(), init_time + time_step)

    def test_default_entity_notify_observers(self):
        entity = Entity("test")
        observer = TestObserver()
        entity.add_observer(observer)
        init_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        time_step = timedelta(seconds=1)
        entity.initialize(init_time)
        for i in range(2):
            entity.tick(time_step)
            self.assertEqual(len(observer.changes_observed), i)
            entity.tock()
            self.assertEqual(len(observer.changes_observed), i+1)
            self.assertEqual(observer.changes_observed[i]["source"], entity)
            self.assertEqual(observer.changes_observed[i]["property_name"], "time")
            self.assertEqual(observer.changes_observed[i]["old_value"], init_time + i*time_step)
            self.assertEqual(observer.changes_observed[i]["new_value"], init_time + (i+1)*time_step)
        