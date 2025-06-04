.. _overview:

Overview
========

Introduction to NOS
------------------

The New Observing Strategies (NOS) initiative within the NASA Earth Science Technology Office Advanced Information Systems Technology program envisions future Earth science missions with distributed sensors (nodes) interconnected by a communications fabric that enables dynamic and intelligent operations. Some NOS concepts resemble systems-of-systems or collaborative systems where operational authority is distributed among multiple systems, necessitating new methods for systems engineering and design to cope with more decentralized control over constituent systems.

NOS-T Architecture
-----------------

NOS-T is best suited for conceptual, systems-level design of NOS components and operational concepts. The system architecture follows a loosely-coupled **event-driven architecture (EDA)** where member nodes communicate through events in the form of notification messages sent over a network.

Key characteristics of the NOS-T architecture:

* **Flexible Node Types**: Nodes can be software applications, simulation models, science databases, or hardware
* **Enhanced Scalability**: The EDA provides scalability and reliability by using consistent event-handling functions
* **Modular Design**: Participants can join and leave experiments without reconfiguring the testbed
* **Security**: Maintains protection of proprietary software and data while enabling cross-organizational tests

Event Broker Infrastructure
--------------------------

The NOS-T architecture relies on a centralized infrastructure component called an **event broker** (or message broker) to exchange event notifications between applications. A broker simplifies communication by requiring each application to connect only to the broker, rather than directly to every other application.

NOS-T adopts **RabbitMQ**, an open-source message broker implementing the Advanced Message Queuing Protocol (AMQP). RabbitMQ uses a publish-subscribe messaging pattern with:

* **Publishers**: Applications that produce events
* **Subscribers**: Applications that consume events
* **Topics**: Categories for event types that applications can publish to or subscribe to

.. mermaid::

   ---
   config:
   theme: redux
   ---
   flowchart LR
   subgraph User_Apps["User Apps"]
      direction TB
         UserApp1["User App 1"]
         UserApp2["User App 2"]
         UserApp3["User App 3"]
   end
      UserApp1 <-. Publish/Subscribe .-> Network["Network"]
      UserApp2 <-. Publish/Subscribe .-> Network
      UserApp3 <-. Publish/Subscribe .-> Network
      Network -- Publish --> EventBroker["Event Broker<br>(AMQP Protocol)"]
      EventBroker -. Subscribe .-> Network
      UserApp1:::red
      UserApp2:::blue
      UserApp3:::green
      Network:::gray
      EventBroker:::darkorange1
      classDef red fill:#ff0000,stroke:#000000,stroke-width:2px
      classDef blue fill:dodgerblue,stroke:#000000,stroke-width:2px
      classDef green fill:#00ff00,stroke:#000000,stroke-width:2px
      classDef gray fill:#808080,stroke:#000000,stroke-width:2px
      classDef darkorange1 fill:#ff8c00,stroke:#000000,stroke-width:2px

System Components
----------------

NOS-T consists of two top-level system components:

1. **User System** (tailored to each test case):
   
   * Consists of user applications developed by users
   * Applications run on separate hosts controlled by each user
   * Can model entire observing systems or individual components (sensors, communication links, algorithms, etc.)
   * Must meet basic NOS-T interface requirements for orchestration

2. **NOS-T System** (fixed for all test cases):

   * Managed by an NOS-T operator
   * Includes the event broker infrastructure
   * Contains a manager application that orchestrates test runs
   * Ensures proper application synchronization, topic configuration, and consistent message structure

.. mermaid::

   ---
   config:
   theme: redux
   ---
   flowchart LR
   subgraph cluster0["User System"]
      direction TB
         PI1["NOS PI"]
         PI2["NOS PI"]
         PI3["NOS PI"]
         UserApp1["User Apps"]
         UserApp2["User Apps"]
         UserApp3["User Apps"]
   end
   subgraph cluster2["NOS-T Operator"]
         EventBroker["Broker<br>(AMQP)"]
         ManagerApplication["Manager"]
         Monitor["Monitor"]
   end
   subgraph cluster1["NOS-T System"]
      direction TB
         NOSTInfrastructure["NOS-T Infrastructure"]
         cluster2
   end
      PI1 --> UserApp1
      PI2 --> UserApp2
      PI3 --> UserApp3
      UserApp1 --> NOSTInfrastructure
      UserApp2 --> NOSTInfrastructure
      UserApp3 --> NOSTInfrastructure
      NOSTInfrastructure --> EventBroker & ManagerApplication & Monitor
      TestCase["NOS Test Case"] --> PI1 & PI2 & PI3
      PI1:::red
      PI2:::blue
      PI3:::green
      UserApp1:::red
      UserApp2:::blue
      UserApp3:::green
      NOSTInfrastructure:::orange
      TestCase:::oval
      classDef red fill:#ff0000,stroke:#000000,stroke-width:2px
      classDef blue fill:dodgerblue,stroke:#000000,stroke-width:2px
      classDef green fill:#00ff00,stroke:#000000,stroke-width:2px
      classDef orange fill:orange,stroke:#333,stroke-width:2px
      classDef oval shape:oval,fill:lightgrey,stroke:#333,stroke-width:2px

   %% Increase the line width of all arrows and change color to black
   linkStyle default stroke-width:3px, stroke:black;

Development Tools
---------------

To aid in application development, the open-source [*]_ NOS-T tools library provides templates for implementing basic NOS-T functionality:

* **Manager application template**: Orchestrates test execution
* **Network Time Protocol (NTP) capabilities**: Synchronizes applications across distributed systems
* **Observer templates**: For implementing sensor applications
* **Observable templates**: For science applications
* **Publisher templates**: For regular messaging (e.g., "heartbeat" messages)
* **Broker connection utilities**: For connecting to the message broker

.. figure:: media/NTP_request.png
   :width: 600
   :align: center
   
   Network Time Protocol (NTP) Round Trip Time Delay

Language Compatibility
--------------------

While the NOS-T tools and most example applications are coded in Python, the system supports multiple programming languages:

* Any language with RabbitMQ interface libraries can be used
* Supported protocols include AMQP and MQTT
* Examples of compatible platforms:

  - JavaScript (used in the "scoreboard" geospatial visualization)
  - MATLAB (via available RabbitMQ libraries)

Applications in a test suite can use different programming languages as long as they maintain a common message structure.
 
.. [*] BSD 3-clause license (Dec. 16, 2021, Reference FY22-005)