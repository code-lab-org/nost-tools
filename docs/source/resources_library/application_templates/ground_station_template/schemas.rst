schemas.py
==========

The schemas.py file defines the message contents and data types that the ground station produces. It is necessary to keep the schema up-to-date if you add further information to the message as it will ensure that the messages are formatted properly.

Ground Station Location
^^^^^^^^^^^^^^^^^^^^^^^

.. autopydantic_settings:: examples.application_templates.ground_station_template.schemas.GroundLocation
   :noindex:
   :settings-show-config-member: True
   :validator-list-fields: True