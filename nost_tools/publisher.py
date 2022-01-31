from abc import ABC, abstractmethod

from .observer import Observer
from .simulator import Mode, Simulator


class ScenarioTimeIntervalPublisher(Observer, ABC):
    """
    Publishes messages at a regular interval (scenario time).

    Provides the simulation with time status messages, also refered to as 'heartbeat messages',
    or 'simulation time statuses'.

    Attributes:
        update_rate (:obj:`timedelta`): Maximum update interval in scenario time.
    """

    def __init__(self, app, time_status_step=None, time_status_init=None):
        self.app = app
        self.time_status_step = time_status_step
        self.time_status_init = time_status_init
        self._next_time_status = None

    @abstractmethod
    def publish_message(self):
        pass

    def on_change(self, source, property_name, old_value, new_value):
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
    Publishes messages at a regular interval (wallclock time). This varies from the ScenarioTimeIntervalPublisher as it publishes
    the current wallclock time, rather than the internal simulation time. This message ensures accurate and synchornized simulation start and end times.

    Attributes:
        update_rate (:obj:`timedelta`): Maximum update interval in wallclock time.
    """

    def __init__(self, app, time_status_step=None, time_status_init=None):
        self.app = app
        self.time_status_step = time_status_step
        self.time_status_init = time_status_init
        self._next_time_status = None

    @abstractmethod
    def publish_message(self):
        pass

    def on_change(self, source, property_name, old_value, new_value):
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
