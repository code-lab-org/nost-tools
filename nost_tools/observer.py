"""
Provides base classes that implement the observer pattern to loosely couple an observable and observer.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, List, Optional, Union

if TYPE_CHECKING:
    from nost_tools.simulator import Mode, Simulator


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

    def __init__(
        self,
        property_filters: Optional[Union[str, List[str]]] = None,
        timestamped: bool = False,
    ):
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
                "new_value": new_value,
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


# Add after the existing Observer class
class MessageObserver(ABC):
    """
    Abstract base class for message observers that can receive RabbitMQ messages.
    """

    @abstractmethod
    def on_message(self, ch, method, properties, body) -> None:
        """Callback for when a message is received.

        Args:
            ch: Channel object
            method: Method frame
            properties: Message properties
            body: Message body
        """
        pass


class MessageObservable(Observable):
    """
    Observable that can notify observers of received messages.
    """

    def __init__(self):
        """Initialize message observable"""
        super().__init__()
        self._message_observers = []

    def add_message_observer(self, observer: MessageObserver) -> None:
        """Add a message observer.

        Args:
            observer (MessageObserver): The observer to add
        """
        self._message_observers.append(observer)

    def remove_message_observer(self, observer: MessageObserver) -> None:
        """Remove a message observer.

        Args:
            observer (MessageObserver): The observer to remove
        """
        self._message_observers.remove(observer)

    def notify_message_observers(self, ch, method, properties, body) -> None:
        """Notify all message observers about a received message.

        Args:
            ch: Channel object
            method: Method frame
            properties: Message properties
            body: Message body
        """
        for observer in self._message_observers:
            observer.on_message(ch, method, properties, body)


class PropertyChangeCallback(Observer):
    """
    Triggers a provided callback basedwhen a named property changes.
    """

    def __init__(self, property_name: str, callback: Callable[[object, object], None]):
        self.callback = callback
        self.property_name = property_name

    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ) -> None:
        if self.property_name == property_name:
            self.callback(source, new_value)


class ScenarioTimeIntervalCallback(Observer):
    """
    Triggers a provided callback at a fixed interval in scenario time.
    """

    def __init__(
        self, callback: Callable[[object, datetime], None], time_inteval: timedelta
    ):
        self.callback = callback
        self.time_interval = time_inteval
        self._next_time = None

    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ):
        if property_name == source.PROPERTY_TIME:
            if self._next_time is None:
                self._next_time = old_value + self.time_interval
            while self._next_time <= new_value:
                self.callback(source, self._next_time)
                self._next_time = self._next_time + self.time_interval


class WallclockTimeIntervalCallback(Observer):
    """
    Triggers a provided callback at a fixed interval in wallclock time.
    """

    def __init__(
        self,
        simulator: "Simulator",
        callback: Callable[[datetime], None],
        time_inteval: timedelta,
        time_init: timedelta = None,
    ):
        self.simulator = simulator
        self.callback = callback
        self.time_interval = time_inteval
        self.time_init = time_init
        self._next_time = None

    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ):
        from nost_tools.simulator import Mode, Simulator

        # Reset timing when resuming
        if (
            property_name == Simulator.PROPERTY_MODE
            and old_value == Mode.RESUMING
            and new_value == Mode.EXECUTING
        ):
            wallclock_now = self.simulator.get_wallclock_time()
            self._next_time = wallclock_now + (self.time_interval if self.time_interval is not None else timedelta())
            return

        if property_name == Simulator.PROPERTY_MODE and new_value == Mode.INITIALIZED:
            self._next_time = self.time_init
        elif property_name == Simulator.PROPERTY_TIME:
            wallclock_time = self.simulator.get_wallclock_time()
            if self._next_time is None:
                self._next_time = wallclock_time + self.time_interval
            while self._next_time <= wallclock_time:
                self.callback(self._next_time)
                self._next_time = self._next_time + self.time_interval
