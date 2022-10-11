NOS-T Tools
===========
This page contains descriptions of the nost_tools library features, and
provides a detailed description of its functions. Within this library, there are
templates to support both time-managed and time-agnostic applications.

These templates allow a user to create an application with unique functionality,
and easily ensure that the application will be compatible with the simulation as
a whole.

In this webpage, you can find the documentation for the provided templates, as
well as several EXAMPLES LINK showing the templates integrated
into a user application.

The tools library is an expansion of the NOS-T testbed infrastructure project, intended to simplify
component interoperability for distributed systems testing. Read more about the NOS-T project in
WHATIS LINK

simulator.py module
-------------------
  *This module provides the structure for a Simulator object to be integrated into a user application*

.. automodule:: nost_tools.simulator
  :members:
  :undoc-members:
  :show-inheritance:

observer.py module
------------------
  *This module provides the structure for an observer object to be integrated into a user application*

.. automodule:: nost_tools.observer
  :members:
  :undoc-members:
  :show-inheritance:

application.py module
---------------------
  *This module provides a template for an example user application that connects to the message broker*

.. automodule:: nost_tools.application
  :members:
  :undoc-members:
  :show-inheritance:

application_utils.py module
---------------------------
  *This module provides supporting utility features that can be integrated into a user application*

.. automodule:: nost_tools.application_utils
  :members:
  :undoc-members:
  :show-inheritance:

entity.py module
----------------
  *This module provides a template for integration with a user application that manages an internal time clock*

.. automodule:: nost_tools.entity
  :members:
  :undoc-members:
  :show-inheritance:

managed_application.py module
-----------------------------
  *This module provides a template for an example user application that connects to the message broker and will receive/have functionality based on messages from the simulation manager*

.. automodule:: nost_tools.managed_application
  :members:
  :undoc-members:
  :show-inheritance:

manager.py module
-----------------
  *This module provides a skeleton manager that can be used to send out commands to direct simulation activity*

.. automodule:: nost_tools.manager
  :members:
  :undoc-members:
  :show-inheritance:

publisher.py module
-------------------
  *This module provides supporting functions for all application functions requiring publication of a message to the broker*

.. automodule:: nost_tools.publisher
  :members:
  :undoc-members:
  :show-inheritance:

schemas.py module
-----------------
  *This module provides an outline of acceptable message schemas and structures*

.. automodule:: nost_tools.schemas
  :members:
  :undoc-members:
  :show-inheritance:
