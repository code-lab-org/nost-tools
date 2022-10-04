Heartbeat
=========

main_heartbeat.py module
------------------------

.. automodule:: scalability.heartbeat.main_heartbeat

.. autoclass:: CustomHeartbeat
	:show-inheritance:
	
.. automethod:: CustomHeartbeat.publish_message

The following code demonstrates how the heartbeat application is started up and how the :obj:`CustomHeartbeat` :obj:`ScenarioTimeIntervalPublisher` object class is initialized and added to the simulator:

.. literalinclude:: /../../scalability/heartbeat/main_heartbeat.py
	:lines: 76-