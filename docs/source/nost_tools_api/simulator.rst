.. _toolsSimObj:

Simulator Objects
=================

Simulator objects structure observer behavior and manage state variables during scenario execution.


Observer Objects
----------------

Observer objects are base classes that implement the observer pattern to loosely couple an observable and observer. 

.. autoclass:: nost_tools.observer.Observer
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.observer.Observable
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.entity.Entity
  :members:
  :show-inheritance:
  
|
  
Scenario Objects
----------------

Scenario objects define states and methods for executing a simulation.

.. autoclass:: nost_tools.simulator.Mode
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.simulator.Simulator
  :members:
  :show-inheritance:
