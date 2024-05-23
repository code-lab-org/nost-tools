import unittest

from nost_tools.observer import Observer, Observable

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
