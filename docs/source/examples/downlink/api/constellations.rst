.. _downlinkConstellations:

Constellations
==============
.. module:: examples.downlink.satellites.main_constellation

.. automodule:: examples.downlink.satellites.main_constellation
  :noindex:
  :show-inheritance:
  :member-order: bysource
  :exclude-members: examples.downlink.satellites.main_constellation.get_elevation_angle, examples.downlink.satellites.main_constellation.check_in_range, examples.downlink.satellites.main_constellation.Constellation, examples.downlink.satellites.main_constellation.PositionPublisher, examples.downlink.satellites.main_constellation


|


Methods
-------
	
.. automethod:: examples.downlink.satellites.main_constellation.get_elevation_angle
	
.. automethod:: examples.downlink.satellites.main_constellation.check_in_range


|


Classes
-------

While the latter methods are globally defined, the following classes have built-in methods that are unique to each object. The :obj:`Constellation` class tracks state transitions for the satellites in the constellation, while the :obj:`PositionPublisher` standardizes the message structure and frequency of published messages updating these states.

Constellation
^^^^^^^^^^^^^

.. autoclass:: examples.downlink.satellites.main_constellation.Constellation
	:show-inheritance:

.. automethod:: examples.downlink.satellites.main_constellation.Constellation.initialize

.. automethod:: examples.downlink.satellites.main_constellation.Constellation.tick

.. automethod:: examples.downlink.satellites.main_constellation.Constellation.tock

.. automethod:: examples.downlink.satellites.main_constellation.Constellation.on_ground

.. automethod:: examples.downlink.satellites.main_constellation.Constellation.on_linkStart

.. automethod:: examples.downlink.satellites.main_constellation.Constellation.on_linkCharge

.. automethod:: examples.downlink.satellites.main_constellation.Constellation.on_outage

.. automethod:: examples.downlink.satellites.main_constellation.Constellation.on_restore

|

PositionPublisher
^^^^^^^^^^^^^^^^^

.. autoclass:: examples.downlink.satellites.main_constellation.PositionPublisher
	:show-inheritance:

.. automethod:: examples.downlink.satellites.main_constellation.PositionPublisher.publish_message


|


Schema
------

.. automodule:: examples.downlink.grounds.ground_config_files.schemas
	:noindex:
	:show-inheritance:
	:member-order: bysource
	:exclude-members: examples.downlink.grounds.ground_config_files.schemas.SatelliteReady, examples.downlink.grounds.ground_config_files.schemas.SatelliteAllReady, examples.downlink.grounds.ground_config_files.schemas.SatelliteStatus, examples.downlink.grounds.ground_config_files.schemas.GroundLocation, examples.downlink.grounds.ground_config_files.schemas.LinkStart, examples.downlink.grounds.ground_config_files.schemas.LinkCharge, examples.downlink.grounds.ground_config_files.schemas.OutageReport, examples.downlink.grounds.ground_config_files.schemas.OutageRestore

.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.SatelliteReady
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.SatelliteAllReady
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.SatelliteStatus
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.GroundLocation
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.LinkStart
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.LinkCharge
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.OutageReport
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.OutageRestore
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource