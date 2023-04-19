.. _satBaseSatellite:

satellite.py
============

.. automodule:: examples.satBaseClass.satellite

The classes have built-in methods that are unique to each object. The :obj:`Satellite` class tracks state transitions for the satellite, while the :obj:`StatusPublisher` standardizes the message structure and frequency of published messages updating these states.

Satellite
---------

.. autoclass:: examples.satBaseClass.satellite.Satellite
	:show-inheritance:

.. automethod:: examples.satBaseClass.satellite.Satellite.initialize

.. automethod:: examples.satBaseClass.satellite.Satellite.tick

.. automethod:: examples.satBaseClass.satellite.Satellite.tock

.. automethod:: examples.satBaseClass.satellite.Satellite.get_min_elevation
	
.. automethod:: examples.satBaseClass.satellite.Satellite.get_sensor_radius
	
.. automethod:: examples.satBaseClass.satellite.Satellite.get_elevation_angle
	
.. automethod:: examples.satBaseClass.satellite.Satellite.check_in_view
	
.. automethod:: examples.satBaseClass.satellite.Satellite.check_in_range

Status Publisher
^^^^^^^^^^^^^^^^

.. autoclass:: examples.satBaseClass.satellite.StatusPublisher
	:show-inheritance: