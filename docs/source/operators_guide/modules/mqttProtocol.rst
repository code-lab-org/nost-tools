MQTT Protocol
=============

*A brief summary of the MQTT protocol with links to detailed resources and a list of useful terminology used throughout this documentation.*

MQTT as a Standard Messaging Protocol
-------------------------------------

MQTT is a Client/Server publish/subscribe messaging protocol that is often used with devices on the Internet of Things (IoT). These devices are often simple remote sensors or controls typically operating with minimal network bandwidth. MQTT is described as a lightweight publish/subscribe messaging transport with minimal code footprint. There are many resources that cover the details and benefits of using the MQTT protocol, including but not limited to:

  * `OASIS Standard MQTT Version 5.0 <https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html>`_
  
  * `MQTT.org <https://mqtt.org>`_  
  
  * `paho-mqtt Python client library <https://pypi.org/project/paho-mqtt/>`_ - (NOTE: This is one of many popular MQTT libraries)

Useful Terminology/Nomenclature
-------------------------------

A deep understanding of the protocol is not necessary to start working with MQTT, but the following are some terms that will be used commonly to explain the NOS-T architecture:

  * broker: 
				A server that receives and routes messages from publisher to subscribers. A broker can be hosted on a local server or in the cloud. NOS-T is hosted on an AWS E2 instance (will hyperlink to section on setting up cloud instance).

  * client: 
				A device or application running an MQTT library and connecting to an MQTT broker over a network. These can range from simple sensors on the IoT to complex servers or even other message brokers.

  * session: 
				An active or remembered (persistent) client connection to the broker with a list of subscriptions. Persistent client connections require a unique :obj:`client_id` and the :obj:`clean_start` = :obj:`False` option enabled on instantiation (see link to section on Configuring Queueing).

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
				
..
	other possible definitions to include: message expiry, session expiry, QoS (linking to Queueing page) 