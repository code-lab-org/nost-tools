Grounds
=======

.. automodule:: firesat.grounds.main_ground
	:exclude-members: Environment
	
|

Class
-----

.. autoclass:: firesat.grounds.main_ground.Environment
  :show-inheritance:

.. automethod:: firesat.grounds.main_ground.Environment.on_change

|

Schema
------

.. automodule:: examples.firesat.satellites.constellation_config_files.schemas
	:noindex:
	:show-inheritance:
	:member-order: bysource
	:exclude-members: examples.firesat.satellites.constellation_config_files.schemas.FireState, examples.firesat.satellites.constellation_config_files.schemas.FireStarted, examples.firesat.satellites.constellation_config_files.schemas.FireDetected, examples.firesat.satellites.constellation_config_files.schemas.FireReported, examples.firesat.satellites.constellation_config_files.schemas.SatelliteStatus, examples.firesat.satellites.constellation_config_files.schemas.GroundLocation

.. autopydantic_settings:: examples.firesat.satellites.constellation_config_files.schemas.GroundLocation
	:noindex:
	:show-inheritance:
	:settings-summary-list-order: bysource
	:member-order: bysource
	
|


Startup Script
--------------

The following code demonstrates how the ground application is started up and how the :obj:`Environment` :obj:`Observer` object class is initialized and added to the simulator:

.. literalinclude:: /../../examples/firesat/grounds/main_ground.py
	:lines: 67-
