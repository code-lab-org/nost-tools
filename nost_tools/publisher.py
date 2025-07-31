"""
Provides utility classes to help applications bind behavior to temporal events.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from .observer import Observer
from .simulator import Mode, Simulator

if TYPE_CHECKING:
    from .application import Application


class ScenarioTimeIntervalPublisher(Observer, ABC):
    """
    Publishes messages at a regular interval (scenario time).

    Provides the simulation with time status messages, also refered to as 'heartbeat messages',
    or 'simulation time statuses'.

    Attributes:
        app (:obj:`Application`): application to publish messages
        time_status_step (:obj:`timedelta`): scenario duration between time status messages
        time_status_init (:obj:`datetime`): scenario time for first time status message
    """

    def __init__(
        self,
        app: "Application",
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
    ):
        """
        Initializes a new scenario time interval publisher.

        Args:
            app (:obj:`Application`): application to publish messages
            time_status_step (:obj:`timedelta`): scenario duration between time status messages
            time_status_init (:obj:`datetime`): scenario time for first time status message
        """
        self.app = app
        self.time_status_step = time_status_step
        self.time_status_init = time_status_init
        self._next_time_status = None
        # TODO: consider adding the `publish_message` callable as an argument rather than abstract method

    @abstractmethod
    def publish_message(self) -> None:
        """
        Publishes a message.
        """
        pass

    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ) -> None:
        """
        Publishes a message after a designated interval of scenario time.

        Args:
            source (object): observable that triggered the change
            property_name (str): name of the changed property
            old_value (obj): old value of the named property
            new_value (obj): new value of the named property
        """
        if property_name == Simulator.PROPERTY_MODE and new_value == Mode.INITIALIZED:
            if self.time_status_init is None:
                self._next_time_status = self.app.simulator.get_init_time()
            else:
                self._next_time_status = self.time_status_init
        elif property_name == Simulator.PROPERTY_TIME:
            while self._next_time_status <= new_value:
                self.publish_message()
                if self.time_status_step is None:
                    self._next_time_status += self.app.simulator.get_time_step()
                else:
                    self._next_time_status += self.time_status_step


class WallclockTimeIntervalPublisher(Observer, ABC):
    """
    Publishes messages at a regular interval (wallclock time).

    Attributes:
        app (:obj:`Application`): application to publish messages
        time_status_step (:obj:`timedelta`): wallclock duration between time status messages
        time_status_init (:obj:`datetime`): wallclock time for first time status message
    """

    def __init__(
        self,
        app: "Application",
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
    ):
        """
        Initializes a new wallclock time interval publisher.

        Args:
            app (:obj:`Application`): application to publish messages
            time_status_step (:obj:`timedelta`): wallclock duration between time status messages
            time_status_init (:obj:`datetime`): wallclock time for first time status message
        """
        self.app = app
        self.time_status_step = time_status_step
        self.time_status_init = time_status_init
        self._next_time_status = None

    @abstractmethod
    def publish_message(self) -> None:
        """
        Publishes a message.
        """
        pass

    def on_change(self, source, property_name, old_value, new_value):
        """
        Publishes a message after a designated interval of scenario time.

        Args:
            source (object): observable that triggered the change
            property_name (str): name of the changed property
            old_value (obj): old value of the named property
            new_value (obj): new value of the named property
        """
        # Reset timing when resuming from pause
        if (
            property_name == Simulator.PROPERTY_MODE
            and old_value == Mode.RESUMING
            and new_value == Mode.EXECUTING
        ):
            self._next_time_status = self.app.simulator.get_wallclock_time()
            if self.time_status_step is not None:
                self._next_time_status += self.time_status_step
            return

        if property_name == Simulator.PROPERTY_MODE and new_value == Mode.INITIALIZED:
            if self.time_status_init is None:
                self._next_time_status = self.app.simulator.get_wallclock_time()
            else:
                self._next_time_status = self.time_status_init
        elif property_name == Simulator.PROPERTY_TIME:
            while self._next_time_status <= self.app.simulator.get_wallclock_time():
                self.publish_message()
                if self.time_status_step is None:
                    self._next_time_status += (
                        self.app.simulator.get_wallclock_time_step()
                    )
                else:
                    self._next_time_status += self.time_status_step
