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

Startup Script
--------------

The following code demonstrates how the fires application is started up, how the :obj:`Environment` :obj:`Observer` object class is initialized and added to the simulator, and how the callback functions are added:

.. literalinclude:: /../../examples/firesat/fires/main_fire.py
	:lines: 136-
