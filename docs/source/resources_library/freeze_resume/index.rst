.. _freezeResume:

Freeze, Resume, and Update System
==================================

As of version 3.0.0, NOS-T supports a distributed freeze/resume/update system that allows managed applications to dynamically request changes to simulation execution. This replaces the previous YAML-based ``time_scale_updates`` configuration.

Overview
--------

The system follows a request-command pattern:

1. A **ManagedApplication** sends a *request* message (e.g., ``FreezeRequest``) to the Manager.
2. The **Manager** receives the request, validates it, and issues a *command* message (e.g., ``FreezeCommand``) to all applications.
3. All applications respond to the command by pausing, resuming, or updating their simulators.

This design ensures that all applications freeze and resume in a coordinated manner, with the Manager maintaining control of the simulation timeline.

.. code-block:: text

   ManagedApplication                Manager                    All Applications
         |                              |                              |
         |--- FreezeRequest ----------->|                              |
         |                              |--- FreezeCommand ----------->|
         |                              |                              | (all pause)
         |                              |                              |
         |--- ResumeRequest ----------->|                              |
         |                              |--- ResumeCommand ----------->|
         |                              |                              | (all resume)

Requesting a Freeze
-------------------

A managed application can request a freeze using the ``request_freeze()`` method:

.. code-block:: python

   # Freeze immediately for 5 minutes
   app.request_freeze(
       freeze_duration=timedelta(minutes=5)
   )

   # Freeze at a specific scenario time for 10 minutes
   app.request_freeze(
       freeze_duration=timedelta(minutes=10),
       sim_freeze_time=datetime(2020, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
   )

   # Indefinite freeze (requires a separate resume request)
   app.request_freeze()

**Parameters:**

- ``freeze_duration`` (Optional[timedelta]): How long to freeze. If ``None``, the freeze is indefinite and requires an explicit resume request.
- ``sim_freeze_time`` (Optional[datetime]): The scenario time at which to freeze. If ``None``, freezes immediately.

Indefinite vs Timed Freezes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Timed freeze**: When ``freeze_duration`` is provided, the Manager will automatically resume after the specified duration elapses.
- **Indefinite freeze**: When ``freeze_duration`` is ``None``, the simulation remains frozen until a managed application explicitly sends a ``ResumeRequest``.

Requesting a Resume
-------------------

A managed application (or unmanaged Application) can request a resume using the ``request_resume()`` method:

.. code-block:: python

   # Resume immediately
   app.request_resume()

   # Resume with a target scenario time and tolerance
   app.request_resume(
       sim_resume_time=datetime(2020, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
       tolerance=timedelta(minutes=30)
   )

**Parameters:**

- ``sim_resume_time`` (Optional[datetime]): Target scenario time for resume. If ``None``, resumes immediately.
- ``tolerance`` (Optional[timedelta]): If provided, the Manager only resumes if the current scenario time is within this tolerance of ``sim_resume_time``. If not provided, defaults to the global ``resume_tolerance`` configuration.

Resume Tolerance
^^^^^^^^^^^^^^^^

The tolerance mechanism allows managed applications to send multiple resume requests, with the Manager only acting when the scenario time is within the specified window. This is useful for applications that periodically check conditions and request resume when appropriate.

**Tolerance behavior:**

- If ``tolerance`` is **not provided**: ``ResumeCommand`` is sent immediately (regardless of ``sim_resume_time``).
- If ``tolerance`` **is** provided with ``sim_resume_time``: The Manager checks if the current scenario time is within tolerance of the requested time.

  - **Within tolerance**: ``ResumeCommand`` is sent immediately.
  - **Outside tolerance**: The request is ignored.

- If only ``tolerance`` is provided (no ``sim_resume_time``): ``ResumeCommand`` is sent immediately.

The global default tolerance can be configured in YAML:

.. code-block:: yaml

   execution:
     general:
       resume_tolerance: "12:00:00"  # 12 hours (default)

Requesting a Time Scale Update
------------------------------

A managed application can request a change to the time scale factor during execution:

.. code-block:: python

   # Update time scale factor immediately
   app.request_update(
       time_scale_factor=120.0
   )

   # Update at a specific scenario time
   app.request_update(
       time_scale_factor=120.0,
       sim_update_time=datetime(2020, 1, 1, 8, 20, 0, tzinfo=timezone.utc)
   )

**Parameters:**

- ``time_scale_factor`` (float): The new time scale factor (scenario seconds per wallclock second).
- ``sim_update_time`` (Optional[datetime]): The scenario time at which to apply the update. If ``None``, updates immediately.

Message Schemas
---------------

The following message schemas are used in the freeze/resume/update system. See the :ref:`API Reference <toolsMsg>` for full field documentation.

**Commands** (Manager to all applications):

- ``FreezeCommand`` / ``FreezeTaskingParameters``
- ``ResumeCommand`` / ``ResumeTaskingParameters``

**Requests** (Managed applications to Manager):

- ``FreezeRequest`` / ``FreezeRequestParameters``
- ``ResumeRequest`` / ``ResumeRequestParameters``
- ``UpdateRequest`` / ``UpdateRequestParameters``
