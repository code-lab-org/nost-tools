.. _downlinkConstellations:

SatelliteStorage
================

.. automodule:: examples.downlink.satelliteStorage.main_satelliteStorage
  :noindex:
  :show-inheritance:
  :member-order: bysource
  :exclude-members: examples.downlink.satelliteStorage.main_satelliteStorage.get_elevation_angle, examples.downlink.satelliteStorage.main_satelliteStorage.check_in_range, examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage, examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage.SatStatePublisher


|


Methods
-------
	
.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.get_elevation_angle
	
.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.check_in_range


|


Classes
-------

While the latter methods are globally defined, the following classes have built-in methods that are unique to each object. The :obj:`SatelliteStorage` class tracks state transitions for the satellites in the constellation, while the :obj:`SatStatePublisher` standardizes the message structure and frequency of published messages updating these states.

SatelliteStorage
^^^^^^^^^^^^^^^^

.. autoclass:: examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage
	:show-inheritance:

.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage.initialize

.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage.tick

.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage.tock

.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage.on_ground

.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage.on_linkStart

.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage.on_linkCharge

.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage.on_outage

.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.SatelliteStorage.on_restore

|

SatStatePublisher
^^^^^^^^^^^^^^^^^

.. autoclass:: examples.downlink.satelliteStorage.main_satelliteStorage.SatStatePublisher
	:show-inheritance:

.. automethod:: examples.downlink.satelliteStorage.main_satelliteStorage.SatStatePublisher.publish_message


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

|
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.SatelliteAllReady
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource

|
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.SatelliteState
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource

|
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.GroundLocation
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource

|
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.LinkStart
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource

|
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.LinkCharge
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource

|
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.OutageReport
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource

|
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.OutageRestore
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource