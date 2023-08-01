.. _toolsUtilObj:

Utility Objects
===============

Utility objects provide supporting functionality for applications.

The ConnectionConfig class packages the information required to establish a connection with the broker.

The ShutDownObserver class is a custom Observer that calls the `shut_down` function for a target application in response to observing a simulator mode change to terminated.

The ScenarioTimeIntervalPublisher class is a custom Observer that publishes a message (via the `publish_message` method) at a regular secnario time interval.
For example, it can be used to publish periodic state updates at a slower frequency than internal state updates necessary to maintain computational accuracy.

The WallclockTimeIntervalPublisher class performs the same duty as ScenarioTimeIntervalPublisher; however, it publishes at a regular wallclock time interval (outside the execution).

The TimeStatusPublisher class further specializes the ScenarioTimeIntervalPublisher behavior to send time status messages used by applications as heartbeat messages.

The ModeStatusObserver class is a custom Observer that publishes mode status messages for debugging during a distributed scenario execution.

.. autoclass:: nost_tools.application_utils.ConnectionConfig
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.application_utils.ShutDownObserver
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.publisher.ScenarioTimeIntervalPublisher
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.publisher.WallclockTimeIntervalPublisher
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.application_utils.TimeStatusPublisher
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.application_utils.ModeStatusObserver
  :members:
  :show-inheritance:
