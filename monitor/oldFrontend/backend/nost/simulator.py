#!/usr/bin/env python

from nost.observer import Observable

from enum import Enum
from datetime import datetime, timedelta, timezone
import time


class Mode(Enum):
    """ This is an enumeration of execution states. """
    UNDEFINED = 0,
    INITIALIZING = 1,
    INITIALIZED = 2,
    EXECUTING = 3,
    TERMINATING = 4,
    TERMINATED = 5


ModeState = {
    0: "Undefined",
    1: "Initializing",
    2: "Initialized",
    3: "Executing",
    4: "Terminating",
    5: "Terminated"
}


class Entity(Observable):
    """ This is the abstract Entity class which inherits the observable. """

    def __init__(self):
        """ Constructor method"""
        super().__init__()

    def initialize(self, init_time):
        """ Abstract method for initializing the entity at an init_time. """
        pass

    def tick(self, time_step):
        """ Abstract method for computing time step durations. """
        pass

    def tock(self):
        """ Abstract method for committing time state change. """
        pass


class Simulator(Observable):
    """ This is the Simulator class which inherit the observable. 
    
    Args:
        wallclock_offset (datetime.timedelta): Offset from the system clock defined by NTP atomic clock, defaults to 0.
        verbose (bool): Determines whether logs are shown.

    Attributes:
        _wallclock_offset (datetime.timedelta): Offset from the system clock defined by NTP atomic clock, defaults to 0.
        _entities (list): List of entities that participate in this simulation.
        _mode (nost.simulator.Mode): Current mode of the simulator.
        _time (datetime.datetime): Current simulation time.
        _next_time (datetime.datetime): Next simulation time.
        _init_time (datetime.datetime): Initial simulation time.
        _time_step (int): Current simulation time step.
        _next_time_step (int): Next simulation time step.
        _duration (int): Current simulation duration.
        _next_duration (int): Next simulation duration.
        _wallclock_epoch (datetime.datetime): Wallclock time when the simulation starts or changes time scaling.
        _simulation_epoch (datetime.datetime): Simulation time when the simulation starts or changes time scaling.
        _time_scale_change_time (datetime.datetime): Simulation time at which to perform a time scale change.
        _time_scale_factor (int): Current relationship between the wallclock time and simulation time.
        _next_time_scale_factor (int): Next relationship between the wallclock time and simulation time.
        _verbose (bool): Determines whether logs are shown.
    """

    def __init__(self, wallclock_offset=timedelta(seconds=0), verbose=False):
        # call super class constructor
        super().__init__()
        self._wallclock_offset = wallclock_offset
        self._entities = []
        self._mode = Mode.UNDEFINED
        self._time = self._next_time = self._init_time = 0
        self._time_step = self._next_time_step = None
        self._duration = self._next_duration = None
        self._wallclock_epoch = None
        self._simulation_epoch = None
        self._time_scale_change_time = None
        self._time_scale_factor = self._next_time_scale_factor = 1
        self._verbose = verbose

    def add_entity(self, entity):
        """ Adds a simulation entity. """
        if self.get_mode() == Mode.INITIALIZING:
            if self._verbose:
                print('Cannot add entity: simulator is initializing')
            return
        elif self.get_mode() == Mode.EXECUTING:
            if self._verbose:
                print('Cannot add entity: simulator is executing')
            return
        elif self.get_mode() == Mode.TERMINATING:
            if self._verbose:
                print('Cannot add entity: simulator is terminating')
            return
        self.set_mode(Mode.UNDEFINED)
        self._entities.append(entity)

    def remove_entity(self, entity):
        """ Removes a simulation entity. """
        if self.get_mode() == Mode.INITIALIZING:
            if self._verbose:
                print('Cannot add entity: simulator is initializing')
            return
        elif self.get_mode() == Mode.EXECUTING:
            if self._verbose:
                print('Cannot add entity: simulator is executing')
            return
        elif self.get_mode() == Mode.TERMINATING:
            if self._verbose:
                print('Cannot add entity: simulator is terminating')
            return
        self.set_mode(Mode.UNDEFINED)
        return self._entities.remove(entity)

    def initialize(self, init_time, wallclock_epoch=None, time_scale_factor=1):
        """ Initializes the simulation to an initial time. """
        if self.get_mode() == Mode.INITIALIZING:
            if self._verbose:
                print('Cannot initialize: simulator is initializing.')
            return
        elif self.get_mode() == Mode.EXECUTING:
            if self._verbose:
                print('Cannot initialize: simulator is executing.')
            return
        elif self.get_mode() == Mode.TERMINATING:
            if self._verbose:
                print('Cannot initialize: simulator is terminating.')
        self.set_mode(Mode.INITIALIZING)
        if self._verbose:
            print('Initializing simulator to time {} (wallclock time {})'.format(
                init_time, wallclock_epoch))
        for entity in self._entities:
            entity.initialize(init_time)
        self._time = self._next_time = self._init_time = init_time
        self._simulation_epoch = init_time
        self._wallclock_epoch = self.get_wallclock_time(
        ) if wallclock_epoch is None else wallclock_epoch
        self._time_scale_factor = self._next_time_scale_factor = time_scale_factor
        self.set_mode(Mode.INITIALIZED)

    def tick(self, time_step):
        """ Computes the state transitions for a time step duration. """
        if self.get_mode() == Mode.TERMINATING:
            return
        elif self.get_mode() != Mode.EXECUTING:
            if self._verbose:
                print('Cannot tick: simulator is not executing')
            return
        for entity in self._entities:
            entity.tick(min(time_step, self._init_time +
                            self._duration - self._time))
        self._next_time = self._time + \
            min(time_step, self._init_time + self._duration - self._time)

    def tock(self):
        """ Commits the state transitions. """
        if self.get_mode() == Mode.TERMINATING:
            return
        elif self.get_mode() != Mode.EXECUTING:
            if self._verbose:
                print('Cannot tock: simulator is not executing')
            return
        if self._verbose:
            print('Commiting simulator state transitions at time {}'.format(self._time))
        for entity in self._entities:
            entity.tock()
        if self._duration != self._next_duration:
            prev_duration = self._duration
            self._duration = self._next_duration
            self.notify_observers('duration', prev_duration, self._duration)
        if self._time_step != self._next_time_step:
            prev_time_step = self._time_step
            self._time_step = self._next_time_step
            self.notify_observers('time_step', prev_time_step, self._time_step)
        if self._time != self._next_time:
            prev_time = self._time
            self._time = self._next_time
            self.notify_observers('time', prev_time, self._time)

    def execute(self, init_time, duration, time_step, wallclock_epoch=None, time_scale_factor=1):
        """ Execute a simulation for a given duration with uniform time steps. """
        self.initialize(init_time, wallclock_epoch, time_scale_factor)
        if self.get_mode() != Mode.INITIALIZED:
            if self._verbose:
                print('Cannot execute: simulator is not initialized.')
            return

        self._duration = self._next_duration = duration
        self.notify_observers('time', self._time, self._time)
        self._time_step = self._next_time_step = time_step
        self.notify_observers('time', self._time, self._time)

        if self._verbose:
            print('Executing simulator for {} ({} steps), starting at {}.'.format(
                duration, time_step, self.get_wallclock_epoch()))
        self.set_mode(Mode.EXECUTING)
        self.wait_for_wallclock_epoch()

        if self._verbose:
            print('Starting main simulation loop.')
        self.notify_observers('time', self._time, self._time)
        while self.get_time() < self.get_init_time() + self.get_duration():
            self.tick(self.get_time_step())
            if self.get_mode() == Mode.TERMINATING:
                break
            if self._time_scale_change_time is not None and self._time_scale_change_time < self._next_time:
                # update the wallclock epoch of this change
                self._wallclock_epoch = self.get_wallclock_time_at_simulation_time(
                    self._time)
                # update the simulation epoch of this change
                self._simulation_epoch = self._time
                # reset the flag to change the time scale factor
                self._time_scale_change_time = None
                # commit the change to the time scale factor and notify observers
                prev_time_scale_factor = self._time_scale_factor
                self._time_scale_factor = self._next_time_scale_factor
                self.notify_observers(
                    'time_scale_factor', prev_time_scale_factor, self._time_scale_factor)
            self.wait_for_tock()
            self.tock()
            if self._verbose:
                print('Simulation advanced to time {}.'.format(self.get_time()))

        self.set_mode(Mode.TERMINATING)
        self.set_mode(Mode.TERMINATED)

        # Remove publish observers
        self.clear_observers()

        if self._verbose:
            print('Simulation executed.')

    def wait_for_tock(self):
        """ Wait to tock until the "correct" next wallclock time. """
        if self.get_time_scale_factor() > 0:
            next_wallclock_time = self.get_wallclock_time_at_simulation_time(
                self._next_time)
            time_diff = next_wallclock_time - self.get_wallclock_time()
            if time_diff > timedelta(seconds=0):
                # print('Waiting for {} to synchronize wallclock.'.format(time_diff))
                time.sleep(time_diff/timedelta(seconds=1))

    def wait_for_wallclock_epoch(self):
        """ Wait to start the simulation until the wallclock epoch. """
        epoch_diff = self.get_wallclock_epoch() - self.get_wallclock_time()
        if epoch_diff > timedelta(seconds=0):
            if self._verbose:
                print('Waiting for {} to synchronize execution start.'.format(epoch_diff))
            time.sleep(epoch_diff/timedelta(seconds=1))

    def get_mode(self):
        """ Get the current simulation mode. """
        return self._mode

    def set_mode(self, mode):
        """ Sets the current simulation state and notifies observers. """
        prev_mode = self._mode
        self._mode = mode
        self.notify_observers('mode', prev_mode, self._mode)

    def get_time_scale_factor(self):
        """ Get the time scale factor (>1 is faster-than-real-time). """
        return self._time_scale_factor

    def get_wallclock_epoch(self):
        """ Get the wallclock epoch. """
        return self._wallclock_epoch

    def get_simulation_epoch(self):
        """ Get the simulation epoch. """
        return self._simulation_epoch

    def get_duration(self):
        """ Get the simulation duration. """
        return self._duration

    def get_init_time(self):
        """ Get the initial simulation time. """
        return self._init_time

    def get_time(self):
        """ Get the simulation time. """
        return self._time

    def get_time_step(self):
        """ Get the simulation time step. """
        return self._time_step

    def get_wallclock_time(self):
        """ Get the current wallclock time. """
        return datetime.now(tz=timezone.utc) + self._wallclock_offset

    def get_wallclock_time_at_simulation_time(self, time):
        """ Get the current wallclock time. """
        return self.get_wallclock_epoch() + (time - self.get_simulation_epoch()) / self.get_time_scale_factor()

    def set_time_scale_factor(self, time_scale_factor, simulation_epoch):
        """ Set the simulation time scale factor (>1 is faster-than-real-time). """
        if self.get_mode() != Mode.EXECUTING:
            if self._verbose:
                print('Can only change time scale factor while executing.')
            return
        if time_scale_factor <= 0:
            if self._verbose:
                print('Time scale factor must be a positive number.')
            return
        self._next_time_scale_factor = time_scale_factor
        self._time_scale_change_time = simulation_epoch

    def set_end_time(self, end_time):
        """ Set the simulation end time. """
        if self.get_mode() != Mode.EXECUTING:
            if self._verbose:
                print('Can only change simulation end time while executing.')
            return
        self.set_duration(end_time - self._init_time)

    def set_duration(self, duration):
        """ Set the simulation duration. """
        if self.get_mode() != Mode.EXECUTING:
            if self._verbose:
                print('Can only change simulation duration while executing.')
            return
        self._next_duration = duration

    def set_time_step(self, time_step):
        """ Set the simulation time step. """
        if self.get_mode() != Mode.EXECUTING:
            if self._verbose:
                print('Can only change simulation time step while executing.')
            return
        self._next_time_step = time_step

    def set_wallclock_offset(self, wallclock_offset):
        """ Set the wallclock offset. """
        if self.get_mode() == Mode.EXECUTING:
            if self._verbose:
                print('Cannot set wallclock offset: simulator is executing')
            return
        elif self.get_mode() == Mode.TERMINATING:
            if self._verbose:
                print('Cannot set wallclock offset: simulator is terminating')
            return
        self._wallclock_offset = wallclock_offset

    def terminate(self):
        """ Terminate the simulation execution. """
        if self.get_mode() != Mode.EXECUTING:
            if self._verbose:
                print('Cannot terminate: simulator is not executing')
            return
        self.set_mode(Mode.TERMINATING)
