.. _overview:

NOS-T Overview
==============

The New Observing Strategies (NOS) initiative within the NASA Earth Science Technology Office Advanced Information Systems Technology program envisions future Earth science missions with distributed sensors (nodes) interconnected by a communications fabric that enables dynamic and intelligent operations. Some NOS concepts resemble systems-of-systems or collaborative systems where operational authority is distributed among multiple systems, necessitating new methods for systems engineering and design to cope with more decentralized control over constituent systems.

NOS-T is best suited for conceptual, systems-level design of NOS components and operational concepts. The NOS-T system architecture follows a loosely-coupled event-driven architecture (EDA) where member nodes communicate state changes through events which take the form of notification messages sent over a network. The nodes in an NOS-T can be software applications, simulation models, science databases, or even hardware. An EDA provides enhanced scalability and reliability over other software architectures by using the same event-handling functions for each test. This allows for a breadboard-like environment where participants can join and leave experiments without having to reconfigure the testbed itself. This modularity makes it easy to conduct various suites of tests spanning organizational boundaries while maintaining security over proprietary software and data.

The NOS-T architecture relies on a centralized infrastructure component called an event broker (synonymous with message broker) to exchange event notifications between applications. A broker greatly simplifies the communication structure because each member application (client) only directly connects to the broker, rather than requiring each application to directly connect to every other application. While there are many alternative broker implementation options available, NOS-T adopts the Solace PubSub+ Standard Edition event broker, a proprietary but freely available commercial product. PubSub+ uses a publish-subscribe messaging pattern which designates applications (clients) as publishers (producers of events) and/or subscribers (consumers of events). Each application can publish and/or subscribe to multiple topics, which are best differentiated along event types.

.. figure:: media/EDA_PubSub_Concept.png
   :width: 600
   :align: center
   
   Event-Driven Architecture with Centralized Broker

The two top-level NOS-T system components, seen in the figure below, include the NOS-T System (fixed for all test cases) and the User System (tailored to each unique test case). The NOS-T System, managed by an NOS-T operator, includes the event broker infrastructure and, generally, a manager application which orchestrates a test run. The operator ensures that constituent applications will be run at the same time, are publishing and subscribing to the correct topics, and use a consistent message structure for events. The manager application, among other tasks, ensures that applications are initialized before starting and maintain a consistent simulation scenario clock.

.. figure:: media/graphicalConcept.png
   :width: 600
   :align: center
   
   NOS-T Graphical Concept

The User System consists of user applications developed and operated by each test case participant. User applications run on separate hosts controlled by each participant and can be variably scoped to model an entire observing system or individual components such as sensors, communication links, tasking or scheduling algorithms, forecasting models, or environmental data (e.g., nature run data sets). Each user application must meet the basic NOS-T interface requirements for orchestration (namely, subscribing and responding to manager commands) plus any additional test case-specific interface requirements agreed upon by the participants. There are no general restrictions on software language, host platform, physical location, or other implementation details for user applications.

To aid in application development, the open-source [*]_ NOS-T tools library contains a set of templates which help users implement basic NOS-T functionality in their test suites. These tools include general templates for constructing new user applications as well as a template for the Manager application referenced above. While users are not required to use the application template to connect to a broker, the template conveniently includes many built-in methods, including Network Time Protocol (NTP) client capabilities. The NTP protocol is a clock request transaction, where a client requests the current time from a server, passing its own time with the request. The server adds its time to the data packet and passes the packet back to the client, providing the client with a reference wallclock offset based on the round trip time delay notionally diagramed in the figure below. These offset calculations can be critical when synchronizing many applications in a common simulation, particularly given potential latencies between applications run in geographically separated locations. 

.. figure:: media/NTP_request.png
   :width: 600
   :align: center
   
   Network Time Protocol (NTP) Round Trip Time Delay

Other templates for observers (i.e. sensor applications), observables (i.e. science applications), publishers (e.g. "heartbeat" messages), and message broker connections are also included in the NOS-T tools library. The documentation for these tools is in the :ref:`nostTools`. 

The tools and most of the applications within the example test suites have been coded in Python. However, other coding languages can interface with the MQTT publish/subscribe protocol. For instance, the “scoreboard” geospatial visualization application seen in many of the examples uses javascript. Furthermore, Matlab has a `built-in function <https://www.mathworks.com/help/thingspeak/mqtt-api.html>`_ that interfaces with an MQTT broker. It is unnecessary for all of the applications in a test suite to use the same coding language as long as they maintain a common message structure for the information passed over the NOS-T infrastructure.
 
   .. [*] BSD 3-clause license (Dec. 16, 2021, Reference FY22-005)
