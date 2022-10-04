Delay
=====

main_delay.py module
--------------------

.. automodule:: scalability.delay.main_delay
	:members: query_nist, post_processing
	:show-inheritance:
	:member-order: bysource

.. autoclass:: HeartbeatDelayRecorder
	

This unmanged application monitors time status updates for any managed application specified by the user. The application records the difference between wallclock time when message published (included in message payload) and wallclock time when message received (checked against local clock with offset from initial NIST query). The following code demonstrates how this unmanaged application connects to the message broker, set up subscriptions to different topics, and add callback functions *without* using the NOS-T tools library.

.. literalinclude:: /../../scalability/delay/main_delay.py
	:lines: 185-