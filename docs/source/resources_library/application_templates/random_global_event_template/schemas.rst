schemas.py
==========

The schemas.py file defines the message contents and data types that the random global events application produces. It is necessary to keep the schema up-to-date if you add further information to the message as it will ensure that the messages are formatted properly.

EventStarted
^^^^^^^^^^^^

.. autopydantic_settings:: examples.application_templates.random_global_event_template.randEvents_config_files.schemas.EventStarted
   :noindex:
   :settings-show-config-member: True
   :validator-list-fields: True
   
EventDayChange
^^^^^^^^^^^^^^

.. autopydantic_settings:: examples.application_templates.random_global_event_template.randEvents_config_files.schemas.EventDayChange
   :noindex:
   :settings-show-config-member: True
   :validator-list-fields: True
   
EventFinished
^^^^^^^^^^^^^

.. autopydantic_settings:: examples.application_templates.random_global_event_template.randEvents_config_files.schemas.EventFinished
   :noindex:
   :settings-show-config-member: True
   :validator-list-fields: True