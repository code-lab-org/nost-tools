"""
Provides base classes that implement the observer pattern to loosely couple an observable and observer.
"""

from abc import ABC, abstractmethod


class Observer(ABC):
    """
    Abstract base class that can be notified of property changes from an associated :obj:`Observable`.
    """

    @abstractmethod
    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ) -> None:
        """Callback notifying of a change.

        Args:
            source (object): object that triggered a property change
            property_name (str): name of the changed property
            old_value (object): old value of the named property
            new_value (object): new value of the named property
        """
        pass


class Observable(object):
    """
    Base class that can register (add/remove) and notify observers of property changes.
    """

    def __init__(self):
        """
        Initializes a new observable.
        """
        # list of observers to be notified of events
        self._observers = []

    def add_observer(self, observer: Observer) -> None:
        """
        Adds an observer to this observable.

        Args:
            observer (:obj:`Observer`): observer to be added
        """
        self._observers.append(observer)

    def remove_observer(self, observer: Observer) -> Observer:
        """
        Removes an observer from this observable.

        Args:
            observer (:obj:`Observer`): obsever to be removed

        Returns:
            :obj:`Observer`: removed observer
        """
        return self._observers.remove(observer)

    def notify_observers(
        self, property_name: str, old_value: object, new_value: object
    ) -> None:
        """
        Notifies observers of a property change.

        Args:
            property_name (str): name of the changed property
            old_value (object): old value of the named property
            new_value (object): new value of the named property
        """
        if old_value != new_value:
            for observer in self._observers:
                observer.on_change(self, property_name, old_value, new_value)
