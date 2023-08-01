Fires
=====

.. automodule:: firesat.fires.main_fire
	:members:
	:noindex:
	:show-inheritance:
	:exclude-members: Environment, on_change, on_fire, on_detected, on_reported
	
|
	
Class
-----

.. autoclass:: firesat.fires.main_fire.Environment
	:show-inheritance:

.. automethod:: firesat.fires.main_fire.Environment.on_change

|

Callback Functions
------------------

.. automethod:: firesat.fires.main_fire.on_fire

.. automethod:: firesat.fires.main_fire.on_detected

.. automethod:: firesat.fires.main_fire.on_reported

|

Schema
------

.. automodule:: examples.firesat.satellites.constellation_config_files.schemas
	:noindex:
	:show-inheritance:
	:member-order: bysource
	:exclude-members: examples.firesat.satellites.constellation_config_files.schemas.FireState, examples.firesat.satellites.constellation_config_files.schemas.FireStarted, examples.firesat.satellites.constellation_config_files.schemas.FireDetected, examples.firesat.satellites.constellation_config_files.schemas.FireReported, examples.firesat.satellites.constellation_config_files.schemas.SatelliteStatus, examples.firesat.satellites.constellation_config_files.schemas.GroundLocation

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

The following code demonstrates how the fires application is started up, how the :obj:`Environment` :obj:`Observer` object class is initialized and added to the simulator, and how the callback functions are added:

.. literalinclude:: /../../examples/firesat/fires/main_fire.py
	:lines: 136-
