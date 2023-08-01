Grounds
=======

.. automodule:: examples.downlink.grounds.main_ground
	:exclude-members: GroundNetwork
		
|

GroundNetwork
-------------

.. autoclass:: examples.downlink.grounds.main_ground.GroundNetwork
  :show-inheritance:

.. automethod:: examples.downlink.grounds.main_ground.GroundNetwork.on_change

.. automethod:: examples.downlink.grounds.main_ground.GroundNetwork.on_ready

.. automethod:: examples.downlink.grounds.main_ground.GroundNetwork.all_ready

.. automethod:: examples.downlink.grounds.main_ground.GroundNetwork.on_commRange

.. automethod:: examples.downlink.grounds.main_ground.GroundNetwork.on_outage

.. automethod:: examples.downlink.grounds.main_ground.GroundNetwork.on_restore

.. automethod:: examples.downlink.grounds.main_ground.GroundNetwork.fixedCost

|

Event Observers
---------------

.. autoclass:: examples.downlink.grounds.main_ground.LinkStartObserver
  :show-inheritance:

.. automethod:: examples.downlink.grounds.main_ground.LinkStartObserver.on_change

|

.. autoclass:: examples.downlink.grounds.main_ground.LinkEndObserver
  :show-inheritance:

.. automethod:: examples.downlink.grounds.main_ground.LinkEndObserver.on_change


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