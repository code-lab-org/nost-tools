.. _fireSatConstellations:

Constellations
==============

.. automodule:: examples.firesat.satellites.main_constellation
  :noindex:
  :show-inheritance:
  :member-order: bysource
  :exclude-members: examples.firesat.satellites.main_constellation.compute_min_elevation, examples.firesat.satellites.main_constellation.compute_sensor_radius, examples.firesat.satellites.main_constellation.get_elevation_angle, examples.firesat.satellites.main_constellation.check_in_view, examples.firesat.satellites.main_constellation.check_in_range, examples.firesat.satellites.main_constellation.Constellation, examples.firesat.satellites.main_constellation.PositionPublisher, examples.firesat.satellites.main_constellation.FireDetectedObserver, examples.firesat.satellites.main_constellation.FireReportedObserver

|

Methods
-------

.. automethod:: examples.firesat.satellites.main_constellation.compute_min_elevation
	
.. automethod:: examples.firesat.satellites.main_constellation.compute_sensor_radius
	
.. automethod:: examples.firesat.satellites.main_constellation.get_elevation_angle
	
.. automethod:: examples.firesat.satellites.main_constellation.check_in_view
	
.. automethod:: examples.firesat.satellites.main_constellation.check_in_range

|

Classes
-------

While the latter methods are globally defined, the following classes have built-in methods that are unique to each object. The :obj:`Constellation` class tracks state transitions for the satellites in the constellation, while the :obj:`PositionPublisher` standardizes the message structure and frequency of published messages updating these states. The :obj:`FireDetectedObserver` and :obj:`FireReportedObserver` objects demonstrate using the :obj:`Observer` class from the NOS-T Tools Library as a triggered message in an event-driven architecture. In this case, messages are triggered by transitions in states of each fire.

Constellation
^^^^^^^^^^^^^

.. autoclass:: examples.firesat.satellites.main_constellation.Constellation
	:noindex:
	:show-inheritance:

.. automethod:: examples.firesat.satellites.main_constellation.Constellation.initialize

.. automethod:: examples.firesat.satellites.main_constellation.Constellation.tick

.. automethod:: examples.firesat.satellites.main_constellation.Constellation.tock

.. automethod:: examples.firesat.satellites.main_constellation.Constellation.on_fire

.. automethod:: examples.firesat.satellites.main_constellation.Constellation.on_ground

|


PositionPublisher
^^^^^^^^^^^^^^^^^

.. autoclass:: examples.firesat.satellites.main_constellation.PositionPublisher
	:show-inheritance:

.. automethod:: examples.firesat.satellites.main_constellation.PositionPublisher.publish_message

|


FireDetectedObserver
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: examples.firesat.satellites.main_constellation.FireDetectedObserver
	:show-inheritance:

.. automethod:: examples.firesat.satellites.main_constellation.FireDetectedObserver.on_change

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
            :lines: 473-481
			
|


FireReportedObserver
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: examples.firesat.satellites.main_constellation.FireReportedObserver
	:show-inheritance:

.. automethod:: examples.firesat.satellites.main_constellation.FireReportedObserver.on_change

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
            :lines: 504-513

|

Schema
------

.. automodule:: examples.firesat.satellites.constellation_config_files.schemas
	:noindex:
	:show-inheritance:
	:member-order: bysource
	:exclude-members: examples.firesat.satellites.constellation_config_files.schemas.FireState, examples.firesat.satellites.constellation_config_files.schemas.FireStarted, examples.firesat.satellites.constellation_config_files.schemas.FireDetected, examples.firesat.satellites.constellation_config_files.schemas.FireReported, examples.firesat.satellites.constellation_config_files.schemas.SatelliteStatus, examples.firesat.satellites.constellation_config_files.schemas.GroundLocation


.. autopydantic_settings:: examples.firesat.satellites.constellation_config_files.schemas.SatelliteStatus
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.firesat.satellites.constellation_config_files.schemas.GroundLocation
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.firesat.satellites.constellation_config_files.schemas.FireStarted
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.firesat.satellites.constellation_config_files.schemas.FireDetected
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.firesat.satellites.constellation_config_files.schemas.FireReported
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource

|


Startup Script
--------------

The following code demonstrates how the :obj:`Constellation` :obj:`Entity` object class is initialized and added to the simulator, how the application is started up, and how callback functions are assigned to the application:

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 518-574 

In this example, six satellites (AQUA, TERRA, SUOMI NPP, NOAA 20, SENTINEL 2A, SENTINEL 2B) are included in the simulation. CelesTrak is queried for current active TLEs, which returns this information as *list* of :obj:`EarthSatellite` objects. A subset *list* of :obj:`EarthSatellite` objects is constructed containing the six satellites of interest. This subset is used for initializing the :obj:`Constellation` :obj:`Entity` before adding to the simulator.
