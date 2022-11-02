import logging

from .observer import Observable

logger = logging.getLogger(__name__)


class Entity(Observable):
    """
    Entity is a class that defines a default simulation entity. A basic simulation entity
    defined through this class can maintain its own scenario clock (time).

    Attributes:
        name (str): The entity name (optional)
    """

    PROPERTY_TIME = "time"

    def __init__(self, name=None):
        super().__init__()
        self.name = name
        self._init_time = self._time = self._next_time = None

    def initialize(self, init_time):
        """
        initialize is a function that activates the entity ('self') at a time of initialization provided by
        the scenario input.

        Args:
            init_time (:obj:`datetime`) : The time of simulation initialization provided by the input scenario
        """
        self._init_time = self._time = self._next_time = init_time

    def tick(self, time_step):
        """
        tick computes the new entity state after an elapsed scenario duration. It is responsible for changing
        the simulation time by the indicated timestep.

        Args:
            time_step (:obj:`timedelta`) : The timedelta that will advance the simulation time (the difference between the current time and the next simulation time)
        """
        self._next_time = self._time + time_step

    def tock(self):
        """
        tock operates along with tick by commiting the new entity state. It changes the simulation time of the
        referenced entity ('self') to the time defined in tick.
        """
        # update the time
        if self._time != self._next_time:
            prev_time = self._time
            self._time = self._next_time
            logger.debug(f"Entity {self.name} updated time to {self._time}.")
            self.notify_observers(self.PROPERTY_TIME, prev_time, self._time)

    def get_time(self):
        """
        get_time computes the new entity state after an elapsed scenario duration for the calling entity ('self').

        Returns:
            :obj:`timedelta`: The current entity time
        """
        return self._time
