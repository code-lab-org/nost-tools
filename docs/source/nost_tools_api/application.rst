.. _toolsAppObj:

Application Objects
===================

These object classes manage communication between a simulator and broker using the MQTT messaging protocol.


Utilities
---------

Utilities monitor and report on application connections, modes, and time statuses. 

.. autoclass:: nost_tools.application_utils.ConnectionConfig
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.application_utils.ShutDownObserver
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.application_utils.TimeStatusPublisher
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.application_utils.ModeStatusObserver
  :members:
  :show-inheritance:
  
|

Publishers
----------

Publishers are useful for state or status messages that update on regular time intervals.

.. autoclass:: nost_tools.publisher.ScenarioTimeIntervalPublisher
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.publisher.WallclockTimeIntervalPublisher
  :members:
  :show-inheritance:

|
  
Applications
------------

These applications serve as templates or wrappers of basic MQTT client functionality and synchronization for simulation.

.. autoclass:: nost_tools.application.Application
  :members:
  :show-inheritance:

.. _toolsMgdApp:

.. autoclass:: nost_tools.managed_application.ManagedApplication
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.manager.TimeScaleUpdate
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.manager.Manager
  :members:
  :show-inheritance:

.. autoclass:: nost_tools.logger_application.LoggerApplication
  :members:
  :show-inheritance:
