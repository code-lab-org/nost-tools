Constellations
==============

main_constellation.py module
----------------------------

.. automodule:: main_constellation
  :members: compute_min_elevation, compute_sensor_radius, get_elevation_angle, check_in_view, check_in_range
  :show-inheritance:
  :member-order: bysource

.. autoclass:: Constellation
	:show-inheritance:	
	
.. automethod:: Constellation.initialize

.. automethod:: Constellation.tick

.. automethod:: Constellation.tock

.. automethod:: Constellation.on_fire

.. automethod:: Constellation.on_ground
	
.. autoclass:: PositionPublisher
	:show-inheritance:	
	
.. automethod:: PositionPublisher.publish_message

.. autoclass:: FireDetectedObserver
	:show-inheritance:
	
.. automethod:: FireDetectedObserver.on_change

.. literalinclude:: /../examples/firesat/satellites/main_constellation.py
            :lines: 499-507
            

.. autoclass:: FireReportedObserver
	:show-inheritance:
	
.. automethod:: FireReportedObserver.on_change

.. literalinclude:: /../examples/firesat/satellites/main_constellation.py
            :lines: 530-539

The following code demonstrates how the constellation application is started up and how the :obj:`Constellation` :obj:`Entity` object class is initialized and added to the simulator:

.. literalinclude:: /../examples/firesat/satellites/main_constellation.py
	:lines: 544-
	
In this example, three satellites (AQUA, TERRA, and SUOMI NPP) are included in the simulation. CelesTrak is queried for current active TLEs, which returns this information as :obj:`list` of :obj:`EarthSatellite` objects. A subset :obj:`list` is constructed containing the three satellites of interest.  