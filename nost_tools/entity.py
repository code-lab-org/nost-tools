"""
Provides a base class to maintain state variables during scenario execution.
"""

import logging
from datetime import datetime, timedelta

from .observer import Observable

logger = logging.getLogger(__name__)


class Entity(Observable):
    """
    A base entity that maintains its own clock (time) during scenario execution.

    Notifies observers of changes to one observable property
     * `time`: current scenario time

    Attributes:
        name (str): The entity name (optional)
    """

    PROPERTY_TIME = "time"

    def __init__(self, name: str = None):
        """
        Initializes a new entity.

        Args:
            name (str): name of the entity (default: None)
        """
        super().__init__()
        self.name = name
        self._init_time = self._time = self._next_time = None

    def initialize(self, init_time: datetime) -> None:
        """
        Initializes the entity at a designated initial scenario time.

        Args:
            init_time (:obj:`datetime`): initial scenario time
        """
        self._init_time = self._time = self._next_time = init_time

    # def tick(self, time_step: timedelta) -> None:
    #     """
    #     Computes the next state transition following an elapsed scenario duration (time step).

    #     Args:
    #         time_step (:obj:`timedelta`): elapsed scenario duration
    #     """
    #     self._next_time = self._time + time_step
    def tick(self, time_step: timedelta) -> None:
        """
        Computes the next state transition following an elapsed scenario duration (time step).
        If the entity hasn't been initialized yet, the time_step will be stored but no
        time advancement will occur until the entity is initialized.

        Args:
            time_step (:obj:`timedelta`): elapsed scenario duration
        """
        if self._time is None:
            logger.debug(
                f"Entity {self.name} not yet initialized, waiting for initialization."
            )
            # Don't try to calculate next_time yet, just maintain the current None state
            return

        self._next_time = self._time + time_step

    def tock(self) -> None:
        """
        Commits the state transition pre-computed in `tick` and notifies observers of changes.
        """
        # update the time
        if self._time != self._next_time:
            prev_time = self._time
            self._time = self._next_time
            logger.debug(f"Entity {self.name} updated time to {self._time}.")
            self.notify_observers(self.PROPERTY_TIME, prev_time, self._time)

    def get_time(self) -> datetime:
        """
        Retrieves the current scenario time.

        Returns:
            :obj:`datetime`: current scenario time
        """
        return self._time
