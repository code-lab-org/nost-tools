Science Event Publisher
=======================

*Unmanaged application that publishes the utility values for random "science events".*

.. automodule:: scienceDash.scienceEventPublisher

The following code is used to set user credentials from a .env file and connect to the broker.

.. literalinclude:: /../../examples/scienceDash/scienceEventPublisher.py
	:lines: 18-31


Next, a loop is created which randomly triggers science events. When triggered, these science
events occur at a random location with a deterministic utility function. The code then publishes
the utility score for each time step until it reaches zero.

.. literalinclude:: /../../examples/scienceDash/scienceEventPublisher.py
	:lines: 33-


