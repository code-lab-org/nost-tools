"""
Provides base classes that implement the observer pattern to loosely couple an observable and observer.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Union


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


class RecordingObserver(Observer):
    """
    Observer that records all changes.
    """

    def __init__(self, property_filters : Optional[Union[str,List[str]]] = None, timestamped : bool = False):
        """
        Initializes a new recording obsever.

        Args:
            properties (Optional[Union[str,List[str]]]): optional list of property names to record
            timestamped (bool): True, if the changes shall be timestamped
        """
        if isinstance(property_filters, str):
            self.property_filters = [property_filters]
        else:
            self.property_filters = property_filters 
        self.changes = []
        self.timestamped = timestamped

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
        if self.property_filters is None or property_name in self.property_filters:
            change = {
                "source": source,
                "property_name": property_name,
                "old_value": old_value,
                "new_value": new_value
            }
            if self.timestamped:
                change["time"] = datetime.now(tz=timezone.utc)
            self.changes.append(change)
        

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
