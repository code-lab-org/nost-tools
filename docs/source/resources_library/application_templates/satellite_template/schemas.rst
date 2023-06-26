.. _satBaseSchemas:

schemas.py
==========

.. automodule:: examples.application_templates.satellite_template.satellite_config_files.schemas

This file contains a pydantic schema for the :obj:`StatusPublisher` object class in the :ref:`satellite.py <satBaseSatellite>` script. It defines the message structure, variables, and their data types. This schema will aid in debugging if your messages are using the wrong data type.

Satellite Status
^^^^^^^^^^^^^^^^

.. autopydantic_settings:: examples.application_templates.satellite_template.satellite_config_files.schemas.SatelliteStatus
   :noindex:
   :settings-show-config-member: True
   :validator-list-fields: True