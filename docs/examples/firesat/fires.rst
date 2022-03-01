Fires
=====

main_fire.py module
-------------------
  
.. automodule:: main_fire
	:members:
	:noindex:
	:show-inheritance:
	:exclude-members: Environment, on_change, on_fire, on_detected, on_reported

.. autoclass:: Environment
	:show-inheritance:
	
.. automethod:: Environment.on_change

.. automethod:: on_fire

.. automethod:: on_detected

.. automethod:: on_reported

The following code demonstrates how the fires application is started up and how the :obj:`Environment` :obj:`Observer` object class is initialized and added to the simulator:

.. literalinclude:: /../examples/firesat/fires/main_fire.py
	:lines: 136-