.. _nostTools:

API Reference
=============

This page contains comprehensive descriptions of the NOS-T tools library features and provides detailed documentation of their functions. The library offers robust support for both time-managed and time-agnostic applications within the Novel Observing Strategies Testbed (NOS-T) ecosystem. Before exploring the API, please complete the :ref:`installation instructions <installation>`.

The tools library implements the event-driven architecture described in the system documentation, organizing ten Python modules into three logical categories:

* **Message Schemas**:
  Define the information carried in common message payloads and the format that information should take using the Pydantic data validation library.
  
  * *Command messages*: Used by the manager to control time-managed scenarios. These include ``InitCommand``, ``StartCommand``, ``StopCommand``, and ``UpdateCommand`` classes. Further described in :ref:`this section <controlEvents>` of the Interface Control Document (ICD).
  
  * *Status messages*: Used by all constituent applications to update simulation time and modes. These include ``ModeStatus``, ``TimeStatus``, and ``ReadyStatus`` classes. Further described in :ref:`this section <statusEvents>` of the ICD.

* **Simulator Objects**:
  Manage state changes and internal clocks for simulation applications.

  * *Observer Objects*: Implement patterns for loosely coupling observables and observers. The ``Observable`` base class allows objects to notify registered ``Observer`` instances of state changes, enabling decoupled event notification.
  
  * *Scenario Objects*: Define states and methods for executing a simulation. The ``Simulator`` class manages simulation state and entities, while the ``Mode`` enumeration defines possible simulation states (IDLE, INIT, EXECUTE, etc.).

* **Applications Objects**:
  Help constituent applications connect to the MQTT message broker and communicate with the MQTT messaging protocol.
  
  * *Utilities*: Monitor and report on application connections, modes, and time statuses. Includes ``ConnectionConfig`` for broker connection management, ``ModeStatusObserver`` for tracking mode changes, and ``TimeStatusPublisher`` for simulation time updates.
  
  * *Publishers*: Define patterns for publishing messages on regularly spaced time-intervals. Includes ``ScenarioTimeIntervalPublisher`` for simulation-time-based intervals and ``WallclockTimeIntervalPublisher`` for real-time intervals.
  
  * *Applications*: Serve as templates or wrappers of basic MQTT client functionality and synchronization for simulation. The ``Application`` base class provides foundation functionality, while ``ManagedApplication`` adds time management features and ``Manager`` orchestrates test execution.

.. toctree::
   :maxdepth: 1
   :hidden:

   schemas
   simulator
   application

.. rubric:: Time Management

A key feature of the NOS-T tools library is its flexible time management system. Applications can operate in:

* **Real-time mode**: Simulation time matches wall clock time
* **Scaled time mode**: Simulation time runs faster or slower than wall clock time
* **Event-driven mode**: Simulation advances based on events rather than continuous time flow

.. rubric:: Integration with Test Suites

The :ref:`NOS-T Example Test Suites <examples>` feature many different implementations of the tools:

* All Python :ref:`FireSat+ <fireSatExampleTop>` applications utilize the NOS-T tools library for faster than real-time simulation with **Manager** coordination
* The Downlink example demonstrates more complex applications with cost modeling
* The Science Dashboard provides a simple unmanaged application pair
* The Scalability tests demonstrate system performance under various loads

Furthermore, the :ref:`example application templates <appTemplates>` include a collection of bare-bones templates, similar to *FireSat+*, with the tools functionality integrated.

.. rubric:: Getting Started

For new users, we recommend:

1. Examine the application templates to understand basic patterns
2. Follow the tutorial to build a simple managed application
3. Explore the examples to see the tools in action