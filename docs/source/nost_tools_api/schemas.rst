.. _toolsMsg:

Message Schemas
===============

Message schemas define the payload syntax and semantics for messages published or subscribed using the AMQP protocol. Schemas work like Python object classes that can easily be serialized to or deserialized from JavaScript Object Notation (JSON) for transmission in AMQP message payloads.


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

Freeze/Resume/Update Messages
-----------------------------

Freeze, resume, and update messages support the distributed freeze/resume system introduced in version 3.0.0. Managed applications send *request* messages to the Manager, which then issues *command* messages to all applications. See :ref:`freezeResume` for usage details.

**Freeze Commands** (Manager to all applications):

.. autopydantic_model:: nost_tools.schemas.FreezeTaskingParameters
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.FreezeCommand
  :members:
  :inherited-members: BaseModel

**Resume Commands** (Manager to all applications):

.. autopydantic_model:: nost_tools.schemas.ResumeTaskingParameters
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.ResumeCommand
  :members:
  :inherited-members: BaseModel

**Freeze Requests** (Managed application to Manager):

.. autopydantic_model:: nost_tools.schemas.FreezeRequestParameters
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.FreezeRequest
  :members:
  :inherited-members: BaseModel

**Resume Requests** (Managed application to Manager):

.. autopydantic_model:: nost_tools.schemas.ResumeRequestParameters
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.ResumeRequest
  :members:
  :inherited-members: BaseModel

**Update Requests** (Managed application to Manager):

.. autopydantic_model:: nost_tools.schemas.UpdateRequestParameters
  :members:
  :inherited-members: BaseModel

.. autopydantic_model:: nost_tools.schemas.UpdateRequest
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
