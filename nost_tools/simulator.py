from enum import Enum
from datetime import datetime, timedelta, timezone
import logging
import time

from .observer import Observable

logger = logging.getLogger(__name__)


class Mode(str, Enum):
    """
    The execution mode of the simulation. It describes the functioning status of the simulation in 6 categories:
    * `UNDEFINED` -- The simulation mode is not assigned to one of the other 5 modes
    * `INITIALIZING` -- The simulation is in the process of initializing (connecting to the broker, establishing simulation varaibles)
    * `INITIALIZED` -- The simulation is ready to begin
    * `EXECUTING` -- The simulation is running with the provided parameters
    * `TERMINATING` -- The simulation is in the process of terminating (disconnecting from the broker)
    * `TERMINATED` -- The simulation has ended
    """

    UNDEFINED = "UNDEFINED"
    INITIALIZING = "INITIALIZING"
    INITIALIZED = "INITIALIZED"
    EXECUTING = "EXECUTING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"


class Simulator(Observable):
    """
    Simulator to process state changes in an application over simulated time.

    A simulator is an observerable object with several properties:
     * `time`: current scenario time
     * `mode`: current execution mode
     * `duration`: scenario execution duration
     * `time_step`: scenario update duration

    Args:
        wallclock_offset (:obj:`timedelta`): System clock offset from a trusted source.
    """

    PROPERTY_MODE = "mode"
    PROPERTY_TIME = "time"

    def __init__(self, wallclock_offset=timedelta(seconds=0)):
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

    def add_entity(self, entity):
        """
        Adds a simulation entity the the simulation.

        Args:
            entity (:obj:`Entity`) : The entity to be added
        """
        if self._mode == Mode.INITIALIZING:
            raise RuntimeError("Cannot add entity: simulator is initializing")
        elif self._mode == Mode.EXECUTING:
            raise RuntimeError("Cannot add entity: simulator is executing")
        elif self._mode == Mode.TERMINATING:
            raise RuntimeError("Cannot add entity: simulator is terminating")
        self._set_mode(Mode.UNDEFINED)
        self._entities.append(entity)

    def get_entities(self):
        """
        Retrieves and returns a list of all entities currently encompassed by the simulation.

        Returns:
            List(Entity) : The list of entities
        """
        # perform shallow copy to prevent external modification
        return self._entities.copy()

    def get_entities_by_name(self, name):
        """
        Returns an entity by name.

        Args:
            name (str) : The entity name

        Returns:
            List(Entity) : The matching entities
        """
        return [entity for entity in self._entities if entity.name == name]

    def get_entities_by_type(self, type):
        """
        Retuens an entity by type (class).

        Args:
            type (Type) : The entity type (class)

        Returns:
            List(Entity) : The matching entities
        """
        return [entity for entity in self._entities if isinstance(entity, type)]

    def remove_entity(self, entity):
        """
        Removes an entity (by name) from a simulation.

        Args:
            entity (:obj:`Entity`) : The entity to be removed
        Returns:
            :obj:`Entity` : The removed entity
        """
        if self._mode == Mode.INITIALIZING:
            raise RuntimeError("Cannot add entity: simulator is initializing")
        elif self._mode == Mode.EXECUTING:
            raise RuntimeError("Cannot add entity: simulator is executing")
        elif self._mode == Mode.TERMINATING:
            raise RuntimeError("Cannot add entity: simulator is terminating")
        if entity in self._entities:
            self._set_mode(Mode.UNDEFINED)
            return self._entities.remove(entity)
        else:
            return None

    def initialize(self, init_time, wallclock_epoch=None, time_scale_factor=1):
        """
        Initializes the simulation to an initial time by transitioning to the INITIALIZING mode, calling the
        `initialize` function for each entity, configuring key private variables,
        and finally transitioning to the INITIALIZED mode.

        Args:
            init_time (:obj:`datetime`): Scenario time at which to start execution.
            wallclock_epoch (:obj:`datetime`): Wallclock time at which to start
                execution, None means to start immediately (default: None).
            time_scale_factor (float): Scenario seconds per wallclock second (default: 1).
        """
        if self._mode == Mode.INITIALIZING:
            raise RuntimeError("Cannot initialize: simulator is initializing.")
        elif self._mode == Mode.EXECUTING:
            raise RuntimeError("Cannot initialize: simulator is executing.")
        elif self._mode == Mode.TERMINATING:
            raise RuntimeError("Cannot initialize: simulator is terminating.")
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
        self, init_time, duration, time_step, wallclock_epoch=None, time_scale_factor=1
    ):
        """
        Execute a simulation for a given duration with uniform time steps as defined in the initilize message from the manager.

        Args:
            init_time (:obj:`datetime`) : The time at which the simulation will initialize.
            duration (:obj:`timedelta`) : The duration of the simulation.
            time_step (:obj:`timedelta`) : The next iterated timestamp for the simulation.
            wallclock_epoch (:obj:`datetime`) : The wallclock timechange (default value: None).
            time_scale_factor (float) : The factor to scale the simulation time in comparison to wallclock time (default value: 1).
        """
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
            self._mode == Mode.EXECUTING
            and self.get_time() < self.get_init_time() + self.get_duration()
        ):
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

    def _wait_for_tock(self):
        """Wait to tock until the "correct" next wallclock time."""
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

    def _wait_for_wallclock_epoch(self):
        """
        Wait to start the simulation until the provided wallclock epoch.

        """
        epoch_diff = self._wallclock_epoch - self.get_wallclock_time()
        if epoch_diff > timedelta(seconds=0):
            logger.info(f"Waiting for {epoch_diff} to synchronize execution start.")
            time.sleep(epoch_diff / timedelta(seconds=1))

    def get_mode(self):
        """
        Returns the current simulation mode.

        Returns:
            :obj:`Mode`: The current simulation mode
        """
        return self._mode

    def _set_mode(self, mode):
        """
        Sets the simulation mode to one of the 6 modes defined in class /Node/.

        Args:
            mode (:obj:`Mode`): The mode to which the simulation will be set.
        """
        prev_mode = self._mode
        self._mode = mode
        self.notify_observers(self.PROPERTY_MODE, prev_mode, self._mode)

    def get_time_scale_factor(self):
        """
        Returns the time scale factor in simulations seconds per wall clock second (>1 is faster-than-real-time) .

        Returns:
            float: The current time scale factor.
        """
        return self._time_scale_factor

    def get_wallclock_epoch(self):
        """
        Returns the wallclock epoch (wallclock time of initial scenario time).

        Returns:
            float: The current wallclock epoch.
        """
        return self._wallclock_epoch

    def get_simulation_epoch(self):
        """
        Returns the simulation epoch (initial scenario time).

        Returns:
            :obj:`datetime`: The current simulation epoch.
        """
        return self._simulation_epoch

    def get_duration(self):
        """
        Returns the simulation duration given by the difference between start and intended stop times.

        Returns:
            :obj:`timedelta`: The current simulation duration.
        """
        return self._duration

    def get_end_time(self):
        """
        Retruns the last timestep as the simulation is terminated, the simulation stop time.

        Returns:
            :obj:`datetime`: The final simulation time.
        """
        return self._init_time + self._duration

    def get_init_time(self):
        """
        Returns the time of simulation initialization.

        Returns:
            :obj:`datetime`: The initial simulation time.
        """
        return self._init_time

    def get_time(self):
        """
        Returns the current simulation time.

        Returns:
            :obj:`datetime`: The current simulation time.
        """
        return self._time

    def get_time_step(self):
        """
        Returns the simulation time step in scenario time.

        Returns:
            :obj:`timedelta`: The current simulation time step (scenario time).
        """
        return self._time_step

    def get_wallclock_time_step(self):
        """
        Returns the simulation time step in wallclock time.

        Returns:
            :obj:`timedelta`: The current simulation time step (wallclock time).
        """
        if self._time_scale_factor is None or self._time_scale_factor <= 0:
            return self._time_step
        else:
            return self._time_step * self._time_scale_factor

    def get_wallclock_time(self):
        """
        Returns the current wallclock time based on standardized NIST time.

        Returns:
            :obj:`datetime`: The current wallclock time, accounting for offset.
        """
        return datetime.now(tz=timezone.utc) + self._wallclock_offset

    def get_wallclock_time_at_simulation_time(self, time):
        """
        Returns the wallclock time corresponding to the given simulation time.

        Args:
            time (:obj:`datetime`): The simulation time for which the wallclock time is being identified.

        Returns:
            :obj:`datetime`: The wallclock time for the identified simulation time
        """
        if self._time_scale_factor is None or self._time_scale_factor <= 0:
            return self.get_wallclock_time()
        else:
            return (
                self._wallclock_epoch
                + (time - self.get_simulation_epoch()) / self._time_scale_factor
            )

    def set_time_scale_factor(self, time_scale_factor, simulation_epoch=None):
        """
        Sets the simulation time scale factor in simulation seconds per wallclock second if the mode allows (>1 is faster-than-real-time).

        Args:
            time_scale_factor (float): The factor to scale the simulation time in comparison to wallclock time.
            simulation_epoch (:obj:`datetime`): The simulation epoch at which the timescale should be set.
        """
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Can only change time scale factor while executing.")
        self._next_time_scale_factor = time_scale_factor
        if simulation_epoch is None:
            self._time_scale_change_time = self._time
        else:
            self._time_scale_change_time = simulation_epoch

    def set_end_time(self, end_time):
        """
        Sets the simulation end time to the provided endtime if the mode allows.

        Args:
            end_time (:obj:`datetime`): The time at which the simulation will end.
        """
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Can only change simulation end time while executing.")
        self.set_duration(end_time - self._init_time)

    def set_duration(self, duration):
        """
        Sets the simulation duration to the provided duration if the mode allows.

        Args:
            duration (:obj:`timedelta`): The duration of the simulation.
        """
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Can only change simulation duration while executing.")
        self._next_duration = duration

    def set_time_step(self, time_step):
        """
        Set the simulation time step to the providede timestep if the mode allows.

        Args:
            time_step (:obj:`timedelta`): The simulation time step.
        """
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Can only change simulation time step while executing.")
        self._next_time_step = time_step

    def set_wallclock_offset(self, wallclock_offset):
        """
        Set the wallclock offset to the provided offset if the mode allows.

        Args:
            wallclock_offset(:obj:`timedelta`): The wallclock offset for the simulation.
        """
        if self._mode == Mode.EXECUTING:
            raise RuntimeError("Cannot set wallclock offset: simulator is executing")
        elif self._mode == Mode.TERMINATING:
            raise RuntimeError("Cannot set wallclock offset: simulator is terminating")
        self._wallclock_offset = wallclock_offset

    def terminate(self):
        """
        Terminates the simulation execution if the mode allows."""
        if self._mode != Mode.EXECUTING:
            raise RuntimeError("Cannot terminate: simulator is not executing")
        self._set_mode(Mode.TERMINATING)
