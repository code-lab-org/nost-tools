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

Startup Script
--------------

The following code demonstrates how the ground application is started up and how the :obj:`Environment` :obj:`Observer` object class is initialized and added to the simulator:

.. literalinclude:: /../../examples/firesat/grounds/main_ground.py
	:lines: 67-
