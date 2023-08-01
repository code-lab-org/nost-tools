.. _toolsAppObj:

Application Templates
=====================

Applications manage communication between a simulator and broker using the MQTT messaging protocol.
They act as templates to provide structure and default behavior for various NOS-T components.

The Application class provides the basic skeleton of a NOS-T application.

The ManagedApplication class adds behaivor required of an application participating in a time-managed execution.

The Manager class implements the behavior required to copordinate a time-managed execution.

The TimeScaleUpdate class is a helper to package the information required to process a time scale update.

The LoggerApplication class implements a basic logging application that records all messages exchanged during a test case execution.

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
