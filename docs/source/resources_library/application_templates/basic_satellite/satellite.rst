.. _satBaseSatellite:

satellite.py
============

.. automodule:: examples.application_templates.basic_satellite.satellite

The classes have built-in methods that are unique to each object. The :obj:`Satellite` class tracks state transitions for the satellite, while the :obj:`StatusPublisher` standardizes the message structure and frequency of published messages updating these states.

Satellite
---------

.. autoclass:: examples.application_templates.basic_satellite.satellite.Satellite
	:show-inheritance:

.. automethod:: examples.application_templates.basic_satellite.satellite.Satellite.initialize

.. automethod:: examples.application_templates.basic_satellite.satellite.Satellite.tick

.. automethod:: examples.application_templates.basic_satellite.satellite.Satellite.tock

.. automethod:: examples.application_templates.basic_satellite.satellite.Satellite.get_min_elevation
	
.. automethod:: examples.application_templates.basic_satellite.satellite.Satellite.get_sensor_radius
	
.. automethod:: examples.application_templates.basic_satellite.satellite.Satellite.get_elevation_angle
	
.. automethod:: examples.application_templates.basic_satellite.satellite.Satellite.check_in_view
	
.. automethod:: examples.application_templates.basic_satellite.satellite.Satellite.check_in_range

Status Publisher
^^^^^^^^^^^^^^^^

.. autoclass:: examples.application_templates.basic_satellite.satellite.StatusPublisher
	:show-inheritance: