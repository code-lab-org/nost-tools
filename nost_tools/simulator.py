"""
Provides classes to execute a simulation.
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Type

from .entity import Entity
from .observer import Observable

logger = logging.getLogger(__name__)


class Mode(str, Enum):
    """
    Enumeration of simulation modes.

    The six simulation modes include
     * `UNDEFINED`: Simulation is in an undefined state that is not one of the other modes.
        For example, the simulation reverts to UNDEFINED after adding a new entity
        and must be re-initialized before execution.
     * `INITIALIZING`: Simulation is in the process of initialization.
     * `INITIALIZED`: Simulation has finished initialization and is ready to execute.
     * `EXECUTING`: Simulation is in the process of execution.
     * `TERMINATING`: Simulation is in the process of termination.
     * `TERMINATED`: Simulation has finished termination and is ready for initialization.
    """

    UNDEFINED = "UNDEFINED"
    INITIALIZING = "INITIALIZING"
    INITIALIZED = "INITIALIZED"
    EXECUTING = "EXECUTING"
    PAUSING = "PAUSING"
    PAUSED = "PAUSED"
    RESUMING = "RESUMING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"


class Simulator(Observable):
    """
    Object that manages simulation of entities in a scenario.

    Notifies observers of changes to observable properties
     * `time`: current scenario time
     * `mode`: current execution mode
     * `duration`: scenario execution duration
     * `time_step`: scenario time step duration
    """

    PROPERTY_MODE = "mode"
    PROPERTY_TIME = "time"

    def __init__(self, wallclock_offset: timedelta = timedelta()):
        """
        Initializes a new simulator.

        Args:
            wallclock_offset (:obj:`timedelta`): difference between the system
                clock and trusted wallclock source (default: zero)
        """
        # call super class constructor
        super().__init__()
        # offset from the system clock to "true" time
        self._wallclock_offset = wallclock_offset
        # list of entities that participate in this simulation
        self._entities = []
        # current mode of the simulator
        self._mode = Mode.UNDEFINED
        # current simulation time; next simulation time, initial simulation time
        self._time = self._next_time = self._init_time = 0
        # current simulation time step; next simulation time step
        self._time_step = self._next_time_step = None
        # current simulation duration; next simulation duration
        self._duration = self._next_duration = None
        # wallclock time when the simulation starts or changes time scaling
        self._wallclock_epoch = None
        # simulation time when the simulation starts or changes time scaling
        self._simulation_epoch = None
        # simulation time at which to perform a time scale change
        self._time_scale_change_time = None
        # relationship between the wallclock time and simulation time
        self._time_scale_factor = self._next_time_scale_factor = 1

    def add_entity(self, entity: Entity) -> None:
        """
        Adds an entity the the simulation.

        Args:
            entity (:obj:`Entity`): entity to be added
        """
        if self._mode not in [Mode.UNDEFINED, Mode.INITIALIZED, Mode.TERMINATED]:
            raise RuntimeError(
                "Can only add entity from UNDEFINED, INITIALIZED, or TERMINATED modes."
            )
        self._set_mode(Mode.UNDEFINED)
        self._entities.append(entity)

    def get_entities(self) -> List[Entity]:
        """
        Retrieves a list of all entities in the simulation.

        Returns:
            List(Entity): list of entities in the simulation
        """
        # perform shallow copy to prevent external modification
        return self._entities.copy()

    def get_entities_by_name(self, name: str) -> List[Entity]:
        """
        Retrieves a list of entities by name.

        Args:
            name (str): name of the entity

        Returns:
            List(Entity): list of entities with a matching name
        """
        return [entity for entity in self._entities if entity.name == name]

    def get_entities_by_type(self, type: Type) -> List[Entity]:
        """
        Retrieves a list of entities by type (class).

        Args:
            type (Type): type (class) of entity

        Returns:
            List(Entity): list of entities with a matching type
        """
        return [entity for entity in self._entities if isinstance(entity, type)]

    def remove_entity(self, entity: Entity) -> Entity:
        """
        Removes an entity from the simulation.

        Args:
            entity (:obj:`Entity`): entity to be removed
        Returns:
            :obj:`Entity`: removed entity
        """
        if self._mode not in [Mode.UNDEFINED, Mode.INITIALIZED, Mode.TERMINATED]:
            raise RuntimeError(
                "Can only remove entity from UNDEFINED, INITIALIZED, or TERMINATED modes."
            )
        if entity in self._entities:
            self._set_mode(Mode.UNDEFINED)
            return self._entities.remove(entity)
        else:
            return None

    def initialize(
        self,
        init_time: datetime,
        wallclock_epoch: datetime = None,
        time_scale_factor: float = 1,
    ) -> None:
        """
        Initializes the simulation to an initial scenario time. Requires that the
        simulator is in UNDEFINED, INITIALIZED, or TERMINATED mode.

        Transitions to the INITIALIZING mode, initializes all entities to the
        initial scenario time, sets the wallclock epoch (wallclock time corresponding
        with the initial scenario time), and finally transitions to the INITIALIZED mode.

        Args:
            init_time (:obj:`datetime`): initial scenario time
            wallclock_epoch (:obj:`datetime`): wallclock time corresponding to the
                initial scenario time, None uses the current wallclock time (default: None)
            time_scale_factor (float): number of scenario seconds per wallclock second (default: 1)
        """
        if self._mode not in [Mode.UNDEFINED, Mode.INITIALIZED, Mode.TERMINATED]:
            raise RuntimeError(
                "Can only initialize from UNDEFINED, INITIALIZED, or TERMINATED modes."
            )
        self._set_mode(Mode.INITIALIZING)
        logger.info(
            f"Initializing simulator to time {init_time} (wallclock time {wallclock_epoch})"
        )
        for entity in self._entities:
            entity.initialize(init_time)
        self._time = self._next_time = self._init_time = init_time
        self._simulation_epoch = init_time
        if wallclock_epoch is None:
            self._wallclock_epoch = self.get_wallclock_time()
        else:
            self._wallclock_epoch = wallclock_epoch
        self._time_scale_factor = self._next_time_scale_factor = time_scale_factor
        self._set_mode(Mode.INITIALIZED)

    def execute(
        self,
        init_time: datetime,
        duration: timedelta,
        time_step: timedelta,
        wallclock_epoch: datetime = None,
        time_scale_factor: float = 1,
    ) -> None:
        """
        Executes a simulation for a specified duration with uniform time steps. Requires that the
        simulator is in UNDEFINED, INITIALIZED, or TERMINATED mode.

        Initializes the simulation (if not already in the INITIALIZED mode), waits for the
        specified wallclock epoch, and transitions to the EXECUTING mode. During execution,
        incrementally performs state transitions for each entity. At the end of the simulation,
        transitions to the TERMINATING and, finally, TERMINATED mode.

        Args:
            init_time (:obj:`datetime`): initial scenario time
            duration (:obj:`timedelta`): scenario execution duration
            time_step (:obj:`timedelta`): scenario time step duration
            wallclock_epoch (:obj:`datetime`): wallclock time corresponding to the
                initial scenario time, None uses the current wallclock time (default: None)
            time_scale_factor (float): number of scenario seconds per wallclock second (default value: 1)
        """
        if self._mode not in [Mode.UNDEFINED, Mode.INITIALIZED, Mode.TERMINATED]:
            raise RuntimeError(
                f"Cannot execute: simulator is {self._mode}. Wait for TERMINATED or terminate the current run."
            )

        if self._mode != Mode.INITIALIZED:
            self.initialize(init_time, wallclock_epoch, time_scale_factor)

        self._duration = self._next_duration = duration
        self._time_step = self._next_time_step = time_step

        logger.info(
            f"Executing simulator for {duration} ({time_step} steps), starting at {self._wallclock_epoch}."
        )
        self._wait_for_wallclock_epoch()
        self._set_mode(Mode.EXECUTING)

        logger.info("Starting main simulation loop.")
        while (
            self._mode == Mode.EXECUTING or self._mode == Mode.PAUSING
        ) and self.get_time() < self.get_init_time() + self.get_duration():
            # compute time step (last step may be shorter)
            time_step = min(
                self._time_step, self._init_time + self._duration - self._time
            )
            # tick each entity
            for entity in self._entities:
                entity.tick(
                    min(time_step, self._init_time + self._duration - self._time)
                )
            # store the next time
            self._next_time = self._time + time_step
            if (
                self._time_scale_change_time is not None
                and self._time_scale_change_time < self._next_time
            ):
                # update the wallclock epoch of this change
                self._wallclock_epoch = self.get_wallclock_time_at_simulation_time(
                    self._time
                )
                # update the simulation epoch of this change
                self._simulation_epoch = self._time
                # reset the flag to change the time scale factor
                self._time_scale_change_time = None
                # commit the change to the time scale factor and notify observers
                prev_time_scale_factor = self._time_scale_factor
                self._time_scale_factor = self._next_time_scale_factor
                self.notify_observers(
                    "time_scale_factor", prev_time_scale_factor, self._time_scale_factor
                )
            # wait for the correct time
            self._wait_for_tock()
            # break out of loop if terminating execution
            if self._mode == Mode.TERMINATING:
                logger.debug("Terminating: exiting execution loop.")
                break
            # tock each entity
            for entity in self._entities:
                entity.tock()
            # update the execution duration, if needed
            if self._duration != self._next_duration:
                prev_duration = self._duration
                self._duration = self._next_duration
                logger.info(f"Updated duration to {self._duration}.")
                self.notify_observers("duration", prev_duration, self._duration)
            # update the execution time step, if needed
            if self._time_step != self._next_time_step:
                prev_time_step = self._time_step
                self._time_step = self._next_time_step
                logger.info(f"Updated time step to {self._time_step}.")
                self.notify_observers("time_step", prev_time_step, self._time_step)
            # update the execution time
            if self._time != self._next_time:
                prev_time = self._time
                self._time = self._next_time
                logger.debug(f"Updated time {self._time}.")
                self.notify_observers(self.PROPERTY_TIME, prev_time, self._time)
            logger.debug(f"Simulation advanced to time {self.get_time()}.")

        logger.info("Simulation complete; terminating.")
        self._set_mode(Mode.TERMINATING)
        self._set_mode(Mode.TERMINATED)

    def _wait_for_tock(self) -> None:
        """
        Waits until the wallclock time matches the next time step interval.
        """
        if self._mode == Mode.PAUSING:
            self._set_mode(Mode.PAUSED)
        while self._mode == Mode.PAUSED:
            time.sleep(0.01)
        if self._mode == Mode.RESUMING:
            # reset the wallclock and simulation epochs
            self._wallclock_epoch = self.get_wallclock_time()
            self._simulation_epoch = self._time
            self._set_mode(Mode.EXECUTING)
        while (
            self._mode == Mode.EXECUTING
            and self.get_wallclock_time_at_simulation_time(self._next_time)
            > self.get_wallclock_time()
        ):
            time_diff = (
                self.get_wallclock_time_at_simulation_time(self._next_time)
                - self.get_wallclock_time()
            )
            if time_diff > timedelta(seconds=0):
                logger.debug(f"Waiting for {time_diff} to advance time.")
                # sleep for up to a second
                time.sleep(min(1, time_diff / timedelta(seconds=1)))

    def _wait_for_wallclock_epoch(self) -> None:
        """
        Waits until the wallclock time matches the designated wallclock epoch.
        """
        epoch_diff = self._wallclock_epoch - self.get_wallclock_time()
        if epoch_diff > timedelta(seconds=0):
            logger.info(f"Waiting for {epoch_diff} to synchronize execution start.")
            time.sleep(epoch_diff / timedelta(seconds=1))

    def get_mode(self) -> Mode:
        """
        Gets the current simulation mode.

        Returns:
            :obj:`Mode`: current simulation mode
        """
        return self._mode

    def _set_mode(self, mode: Mode) -> None:
        """
        Sets the simulation mode and notifies observers.

        Args:
            mode (:obj:`Mode`): new simulation mode
        """
        prev_mode = self._mode
        self._mode = mode
        self.notify_observers(self.PROPERTY_MODE, prev_mode, self._mode)

    def get_time_scale_factor(self) -> float:
        """
        Gets the time scale factor in scenario seconds per wall clock second (>1 is faster-than-real-time).

        Returns:
            float: current time scale factor
        """
        return self._time_scale_factor

    def get_wallclock_epoch(self) -> datetime:
        """
        Gets the wallclock epoch.

        Returns:
            :obj:`datetime`: current wallclock epoch
        """
        return self._wallclock_epoch

    def get_simulation_epoch(self) -> datetime:
        """
        Gets the scenario epoch.

        Returns:
            :obj:`datetime`: current scenario epoch
        """
        return self._simulation_epoch

    def get_duration(self) -> timedelta:
        """
        Gets the scenario duration.

        Returns:
            :obj:`timedelta`: current scenario duration
        """
        return self._duration

    def get_end_time(self) -> datetime:
        """
        Gets the scenario end time.

        Returns:
            :obj:`datetime`: final scenario time
        """
        return self._init_time + self._duration

    def get_init_time(self) -> datetime:
        """
        Gets the initial scenario time.

        Returns:
            :obj:`datetime`: initial scenario time
        """
        return self._init_time

    def get_time(self) -> datetime:
        """
        Gets the current scenario time.

        Returns:
            :obj:`datetime`: current scenario time
        """
        return self._time

    def get_time_step(self) -> timedelta:
        """
        Gets the scenario time step duration.

        Returns:
            :obj:`timedelta`: time step duration
        """
        return self._time_step

    def get_wallclock_time_step(self) -> timedelta:
        """
        Gets the wallclock time step duration.

        Returns:
            :obj:`timedelta`: time step duration
        """
        if self._time_scale_factor is None or self._time_scale_factor <= 0:
            return self._time_step
        else:
            return self._time_step * self._time_scale_factor

    def get_wallclock_time(self) -> datetime:
        """
        Gets the current wallclock time.

        Returns:
            :obj:`datetime`: current wallclock time
        """
        return datetime.now(tz=timezone.utc) + self._wallclock_offset

    def get_wallclock_time_at_simulation_time(self, time: datetime) -> datetime:
        """
        Gets the wallclock time corresponding to the designated scenario time.

        Args:
            time (:obj:`datetime`): scenario time

        Returns:
            :obj:`datetime`: wallclock time
        """
        if self._time_scale_factor is None or self._time_scale_factor <= 0:
            return self.get_wallclock_time()
        else:
            return (
                self._wallclock_epoch
                + (time - self.get_simulation_epoch()) / self._time_scale_factor
            )

    def set_time_scale_factor(
        self, time_scale_factor: float, simulation_epoch: datetime = None
    ) -> None:
        """
        Sets the time scale factor in scenario seconds per wallclock second
        (>1 is faster-than-real-time). Requires that the simulator is in EXECUTING mode.

        Args:
            time_scale_factor (float): number of scenario seconds per wallclock second
            simulation_epoch (:obj:`datetime`): scenario time at which the time scale factor changes
        """
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Can only change time scale factor while executing.")
        self._next_time_scale_factor = time_scale_factor
        if simulation_epoch is None:
            self._time_scale_change_time = self._time
        else:
            self._time_scale_change_time = simulation_epoch

    def set_end_time(self, end_time: datetime) -> None:
        """
        Sets the scenario end time. Requires that the simulator is in EXECUTING mode.

        Args:
            end_time (:obj:`datetime`): scenario end time
        """
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Can only change scenario end time while executing.")
        self.set_duration(end_time - self._init_time)

    def set_duration(self, duration: timedelta) -> None:
        """
        Sets the scenario duration. Requires that the simulator is in EXECUTING mode.

        Args:
            duration (:obj:`timedelta`): scenario duration
        """
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Can only change scenario duration while executing.")
        self._next_duration = duration

    def set_time_step(self, time_step: timedelta) -> None:
        """
        Set the scenario time step duration. Requires that the simulator is in EXECUTING mode.

        Args:
            time_step (:obj:`timedelta`): scenario time step duration
        """
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Can only change scenario time step while executing.")
        self._next_time_step = time_step

    def set_wallclock_offset(self, wallclock_offset: timedelta) -> None:
        """
        Set the wallclock offset (difference between system clock and trusted wallclock source).
        Requires that the simulator is in UNDEFINED, INITIALIZING, INITIALIZED, or TERMINATED mode.

        Args:
            wallclock_offset(:obj:`timedelta`): difference between system clock and trusted wallclock source
        """
        if self._mode == Mode.TERMINATING:
            raise RuntimeError("Cannot set wallclock offset: simulator is terminating")
        self._wallclock_offset = wallclock_offset

    def pause(self) -> None:
        """
        Pauses the scenario execution. Requires that the simulator is in EXECUTING mode.
        """
        logger.info(f"Pausing simulation execution at {self._time}.")
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Cannot pause: simulator is not executing.")

        self._set_mode(Mode.PAUSING)

    def resume(self) -> None:
        """
        Resumes the scenario execution. Requires that the simulator is in PAUSING or PAUSED mode.
        """
        if self._mode not in [Mode.PAUSING, Mode.PAUSED]:
            raise RuntimeError("Cannot resume: simulator is not pausing or paused.")
        self._set_mode(Mode.RESUMING)

    def terminate(self) -> None:
        """
        Terminates the scenario execution. Requires that the simulator is in EXECUTING mode.
        """
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Cannot terminate: simulator is not executing.")
        self._set_mode(Mode.TERMINATING)
