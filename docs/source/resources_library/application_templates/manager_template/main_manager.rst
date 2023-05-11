.. _satBaseManager:

main_manager.py
===============

This script is the entry point code for the NOS-T manager. You must start main_manager.py *after* managed applications are able to initialize.


This manager application leverages the manager template in the NOS-T tools library. The manager template is designed to publish information to specific topics, and any applications using the :ref:`Managed Application <toolsMgdApp>` object class will subscribe to these topics to know when to start and stop simulations, as well as the resolution and time scale factor of the simulation steps.

.. literalinclude:: /../../examples/application_templates/manager_template/main_manager.py
  :lines: 3-