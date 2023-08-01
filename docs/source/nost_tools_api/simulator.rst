.. _toolsSimObj:

Simulator Objects
=================

Simulator objects manage entity state variables during scenario execution.

Observer and Observable classes implement the observer pattern using the `observer pattern <https://en.wikipedia.org/wiki/Observer_pattern>`_ for loose coupling of behavior between objects.
They are primarily building-blocks for other classes within the library.

The Entity class is a base simulation component that maintains stateful properties such as a simulation clock (i.e., the time). 
As an Observable, an Entity object notifies any bound Observers when its `time` property changes. 
The Entity class has stub methods to manage simulation state including `initialize` (before start of a new execution), `tick` (compute the next state variables during a time step interval), and `tock` (commit the next state variables at the time step boundary).
Typically, users will create a custom Entity subclass to specialize behavior for a particular simulation entity. 

The Simulation class manages scenario time advancement for an execution consisting of member Entity objects.
As an Observable, a Simulation object notifies any bound Observers when any of its properties change including `time`, `mode`, `time_scale_factor`, `duration`, or `time_step`.
The Simulator class has methods to manage simulation execution including `initialize` (prepares a new execution),  `execute` (runs a new execution), and `terminate` (prematurely end an execution).
When intitialized, a Simulator will initialize all member Entity objects.
When executed, a Simulator will sequentially compute the next time step boundary, call `tick` on all member Entity objects to compute the next state, wait until the appropriate wallclock time, and finally call `tock` on all member Entity objects to process the state change.
Timing options during initialization and execution specify the starting and ending scenario time, starting wallclock time, scenario time step duration (i.e., time interval between state updates), time scale factor (i.e., number of scenario seconds per wallclock second).

.. autoclass:: nost_tools.observer.Observer
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.observer.Observable
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.entity.Entity
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.simulator.Mode
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.simulator.Simulator
  :members:
  :show-inheritance:
