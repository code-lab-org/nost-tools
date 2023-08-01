MQTT Protocol
=============

*A brief summary of the MQTT protocol with links to detailed resources and a list of useful terminology used throughout this documentation.*

MQTT as a Standard Messaging Protocol
-------------------------------------

MQTT is a Client/Server publish/subscribe messaging protocol that is often used with devices on the Internet of Things (IoT). These devices are often simple remote sensors or controls typically operating with minimal network bandwidth. MQTT is described as a lightweight publish/subscribe messaging transport with minimal code footprint. There are many resources that cover the details and benefits of using the MQTT protocol, including but not limited to:

  * `OASIS Standard MQTT Version 5.0 <https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html>`_
  
  * `MQTT.org <https://mqtt.org>`_  
  
  * `paho-mqtt Python client library <https://pypi.org/project/paho-mqtt/>`_ - (NOTE: This is one of many popular MQTT libraries)

|

Useful Terminology/Nomenclature
-------------------------------

A deep understanding of the protocol is not necessary to start working with MQTT, but the following are some terms that will be used commonly to explain the NOS-T architecture:

  * broker: 
				A server that receives and routes messages from publisher to subscribers. A broker can be hosted on a local server or in the cloud. NOS-T is hosted on an Amazon Elastic Compute Cloud (EC2) instance.

  * client: 
				A device or application running an MQTT library and connecting to an MQTT broker over a network. These can range from simple sensors on the IoT to complex servers or even other message brokers.

  * session: 
				An active or remembered (persistent) client connection to the broker with a list of subscriptions. Persistent client connections require a unique :obj:`client_id` and the :obj:`clean_start` = :obj:`False` option enabled on instantiation, which would be necessary to enable asynchronous message queuing.

  * publish/subscribe (pub/sub):
				An architectural pattern that decouples the clients that send messages from the clients that receive messages. In the pub/sub model, publishers and subscribers never contact each other directly. The connection is handled by a broker that filters all incoming messages and distributes them correctly to subscribers.
  
  * topic: 
				An MQTT-form of addressing with forward-slashes. For NOS-T topics we use the convention: {PREFIX}/{APP_NAME}/{TOPIC_NAME}

  * publisher: 
				A client that sends a message payload to a specified topic. Note that published messages are unique, but more than one client can publish to the same topic unless access control rules are imposed. 

  * subscriber:
				A client that receives a message payload from a specified topic, routed through the message broker. Note that many clients can subscribe to the same topic unless access control rules are imposed.
				
  * payload:
				The actual content of an MQTT message. MQTT is a binary based protocol where messages are typically referred to as packets. A packet includes a header, with binary control codes indicating type and size of the message, and a data-agnostic payload in the form of a binary encoded message.

|

Subscriptions using Wildcard Characters
---------------------------------------

While a publisher needs to specify the topic endpoint where the message is sent, adopting a hierarchical structure for these endpoints with forward slashes as topic-level separators creates a convenient way to subscribe to many messages and filter for the subset of messages that matter. These multitopic subscriptions are enabled by the use of `wildcard` charachters.  

The most useful wildcard character is the **'#'** sign *at the end* of a topic's address, which indicates to the broker that this client is subscribing to *all* messages at this topic level and below. For example, if a user adopts the previously introduced NOS-T topics convention, it is really simple to create a subscription to all messages from a specific application by subscribing to {PREFIX}/{APP_NAME}/#. This wildcard character should be used with caution, however, because the subscribing client may not be able to process the volume of concurrent message payloads. Generally, multi-level wildcards are not recommended for this reason, although using this approach for the :ref:`NOS-T Web-based Monitor For Broker<webMonitor>` allows an operator to track all the messages on a {PREFIX} and filter by application names and/or specific topic endpoints, which has proven to be an essential debugging tool for the development team.

Another useful wildcard character is the **'+'** sign *within* a topic's address, which indicates a single level of abstraction for subscription. For example, a common message sent by all applications subscribing to manager messages is a mode status message. The topic-structure for these status messages is consistently {PREFIX}/{APP_NAME}/status, and thus an application can be designed to monitor *all* status messages by subscribing to {PREFIX}/+/status.

..
	other possible definitions to include: message expiry, session expiry, QoS (linking to Queueing page) 