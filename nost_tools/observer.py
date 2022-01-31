from abc import ABC, abstractmethod


class Observer(ABC):
    """
    An Observer is an abstract base class that can be notified of property changes in an assigned application, and can record
    the logistics of that change for internal referencing.
    """

    @abstractmethod
    def on_change(self, source, property_name, old_value, new_value):
        """Callback notifying of a change.

        Args:
            source (:obj:`Observable`): The observervable that triggered the change.
            property_name (str): The name of property that is changing.
            old_value (obj): The old value of the named property.
            new_value (obj): The new value of the named property.
        """
        pass


class Observable(object):
    """

    An Observable is a base class that can register (add/remove) and notify observers of
    property changes. The property changes occur **to** the observable.
    """

    def __init__(self):
        # list of observers to be notified of events
        self._observers = []

    def add_observer(self, observer):
        """
        Adds an observer to the referenced object ('self').

        Args:
            observer (:obj:`Observer`): The observer object to be observed.
        """
        self._observers.append(observer)

    def remove_observer(self, observer):
        """
        Removes an observer from the referenced object ('self').

        Args:
            observer (:obj:`Observer`): The observer object to no longer be observed.

        Returns:
            :obj:`Observer`: The observer object that was removed.
        """
        return self._observers.remove(observer)

    def notify_observers(self, property_name, old_value, new_value):
        """
        Notifies observers of a property change in the referenced object ('self').

        Args:
            property_name (str): The name of property that is changing.
            old_value (obj): The old value of the named property.
            new_value (obj): The new value of the named property.
        """
        if old_value != new_value:
            for observer in self._observers:
                observer.on_change(self, property_name, old_value, new_value)
