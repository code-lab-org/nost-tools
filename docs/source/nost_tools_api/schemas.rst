.. _toolsMsg:

Message Schemas
===============

Message schemas define the payload syntax and semantics for messages published or subscribed using the MQTT protocol.


Command Messages
----------------

Command messages are published by the manager application during scenario execution.

.. autopydantic_model:: nost_tools.schemas.InitTaskingParameters
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.InitCommand
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.StartTaskingParameters
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.StartCommand
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.StopTaskingParameters
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.StopCommand
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.UpdateTaskingParameters
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.UpdateCommand
  :members:
  :inherited-members: BaseModel

|
  
Status Messages
---------------

Status messages are published by all applications during scenario execution.

.. autopydantic_model:: nost_tools.schemas.TimeStatusProperties
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.TimeStatus
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.ModeStatusProperties
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.ModeStatus
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.ReadyStatusProperties
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.ReadyStatus
  :members:
  :inherited-members: BaseModel
