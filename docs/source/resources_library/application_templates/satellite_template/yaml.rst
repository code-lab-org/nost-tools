.. _satBaseConfig:

template.yaml
=============

The satellite application reads its connection and execution settings from a YAML configuration file, so a scenario can be changed without editing any Python.

Under ``servers``, the ``rabbitmq`` block identifies the broker and how to authenticate against it. Under ``execution``, the ``general`` block sets the :obj:`prefix` for the channel the satellite publishes its messages to. The prefix is currently :obj:`template`, and must be set consistently across every application in your test case, otherwise they will never start up together.

The ``managed_applications`` section holds settings specific to this application: the time scale factor relating wallclock seconds to scenario seconds, the time step, the interval between time status "heartbeat" messages, and :obj:`manager_app_name`, which names the manager whose command messages this application follows.

Application-specific values live under :obj:`configuration_parameters`, and are reached in Python through ``config.rc.application_configuration`` once the configuration is loaded with an ``app_name``. Here that is :obj:`SATELLITE_NAME`, currently :obj:`SUOMI NPP`, which pulls a spacecraft's current TLEs from `Celestrak <https://celestrak.com/NORAD/elements/active.txt>`_ to model the orbit. The spacecraft name *must* exactly match the name found on Celestrak, including the upper-case letters.

.. literalinclude:: /../../examples/application_templates/satellite_template/template.yaml
  :language: yaml
