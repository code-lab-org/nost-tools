Basic Satellite
===============

This set of Python scripts model a basic satellite that can be extended for various functions. 


satellite.py
------------

Coming Soon!

.. automodule:: examples.satBaseClass.main_sat


Classes
-------

While the latter methods are globally defined, the following classes have built-in methods that are unique to each object. The :obj:`Satellite` class tracks state transitions for the satellite, while the :obj:`StatusPublisher` standardizes the message structure and frequency of published messages updating these states.

Constellation
^^^^^^^^^^^^^

.. autoclass:: examples.satBaseClass.satellite.Satellite
	:show-inheritance:

Status Publisher
^^^^^^^^^^^^^^^^

.. autoclass:: examples.satBaseClass.satellite.StatusPublisher
	:show-inheritance: