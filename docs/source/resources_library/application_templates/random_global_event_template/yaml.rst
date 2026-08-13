template.yaml
=============

The application reads its connection and execution settings from a YAML configuration file, so a scenario can be changed without editing any Python.

Under ``servers``, the ``rabbitmq`` block identifies the broker and how to authenticate against it. Under ``execution``, the ``general`` block sets the :obj:`prefix` for the channel this application publishes to, which must match the prefix used by every other application in the test case. The :obj:`time_scale_factor` is set to 3600, so one wallclock second advances the scenario by one hour.

The event settings live under :obj:`configuration_parameters`, and are reached in Python through ``config.rc.application_configuration`` once the configuration is loaded with an ``app_name``. They set the number of events and the maximum duration for any event, along with the range of scenario time within which events can occur. Random draws determine each event's start and finish time, triggering the relevant messages at the appropriate scenario time.

Leave :obj:`SEED` blank to generate a new random sequence on every run, or set an integer for repeatable results.

.. literalinclude:: /../../examples/application_templates/random_global_event_template/template.yaml
  :language: yaml
