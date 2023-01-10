Constellations
==============

examples.firesat.satellites.main_constellation.py module
--------------------------------------------------------

.. automodule:: examples.firesat.satellites.main_constellation
  :members: compute_min_elevation, compute_sensor_radius, get_elevation_angle, check_in_view, check_in_range
  :show-inheritance:
  :member-order: bysource

.. autoclass:: examples.firesat.satellites.main_constellation.Constellation
	:show-inheritance:

.. automethod:: examples.firesat.satellites.main_constellation.Constellation.initialize

.. automethod:: examples.firesat.satellites.main_constellation.Constellation.tick

.. automethod:: examples.firesat.satellites.main_constellation.Constellation.tock

.. automethod:: examples.firesat.satellites.main_constellation.Constellation.on_fire

.. automethod:: examples.firesat.satellites.main_constellation.Constellation.on_ground

.. autoclass:: examples.firesat.satellites.main_constellation.PositionPublisher
	:show-inheritance:

.. automethod:: examples.firesat.satellites.main_constellation.PositionPublisher.publish_message

.. autoclass:: examples.firesat.satellites.main_constellation.FireDetectedObserver
	:show-inheritance:

.. automethod:: examples.firesat.satellites.main_constellation.FireDetectedObserver.on_change

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
            :lines: 499-507


.. autoclass:: examples.firesat.satellites.main_constellation.FireReportedObserver
	:show-inheritance:

.. automethod:: examples.firesat.satellites.main_constellation.FireReportedObserver.on_change

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
            :lines: 530-539

The following code demonstrates how the constellation application is started up and how the :obj:`Constellation` :obj:`Entity` object class is initialized and added to the simulator:

.. literalinclude:: /../../examples/firesat/satellites/main_constellation.py
	:lines: 544-

In this example, six satellites (AQUA, TERRA, SUOMI NPP, NOAA 20, SENTINEL 2A, SENTINEL 2B) are included in the simulation. CelesTrak is queried for current active TLEs, which returns this information as *list* of :obj:`EarthSatellite` objects. A subset *list* is constructed containing the six satellites of interest.
