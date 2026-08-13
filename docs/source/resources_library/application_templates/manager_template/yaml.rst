template.yaml
=============

The manager reads its connection and execution settings from a YAML configuration file, so a test case can be changed without editing any Python.

Two sections matter most. Under ``servers``, the ``rabbitmq`` block identifies the broker and how to authenticate against it. Under ``execution``, the ``general`` block sets the :obj:`prefix`, which determines the topic the manager publishes its command messages to. You *must* ensure that every managed application in your test case uses the same prefix, otherwise they will never start up.

The ``manager`` block defines the test case itself: the scenario window, the time step, the time scale factor relating wallclock seconds to scenario seconds, and the lead time between a scheduled command and the action it triggers. The :obj:`required_apps` list names the applications that must report ready before execution begins; the manager excludes itself from that wait.

Time scale changes during a run are still supported, but they are made programmatically rather than declared in advance. An application can request one at any point during execution, and the manager publishes the corresponding update command. See the ``Manager`` class in :ref:`the application API documentation <toolsAppObj>` for the methods involved.

.. literalinclude:: /../../examples/application_templates/manager_template/template.yaml
  :language: yaml
