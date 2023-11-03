Outages
=======

.. automodule:: examples.downlink.outages.main_outages
	:exclude-members: examples.downlink.outages.main_outages.Scheduler, examples.downlink.outages.main_outages.Randomizer

|

Scheduler
---------

.. autoclass:: examples.downlink.outages.main_outages.Scheduler
  :show-inheritance:

.. automethod:: examples.downlink.outages.main_outages.Scheduler.on_ground

.. automethod:: examples.downlink.outages.main_outages.Scheduler.on_change


|


Randomizer
----------

.. autoclass:: examples.downlink.outages.main_outages.Randomizer
  :show-inheritance:
  
.. automethod:: examples.downlink.outages.main_outages.Randomizer.publish_message


|


Schema
------

.. automodule:: examples.downlink.grounds.ground_config_files.schemas
	:noindex:
	:show-inheritance:
	:member-order: bysource
	:exclude-members: examples.downlink.grounds.ground_config_files.schemas.SatelliteReady, examples.downlink.grounds.ground_config_files.schemas.SatelliteAllReady, examples.downlink.grounds.ground_config_files.schemas.SatelliteStatus, examples.downlink.grounds.ground_config_files.schemas.GroundLocation, examples.downlink.grounds.ground_config_files.schemas.LinkStart, examples.downlink.grounds.ground_config_files.schemas.LinkCharge, examples.downlink.grounds.ground_config_files.schemas.OutageReport, examples.downlink.grounds.ground_config_files.schemas.OutageRestore
	
.. autopydantic_settings:: examples.downlink.grounds.ground_config_files.schemas.GroundLocation
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
