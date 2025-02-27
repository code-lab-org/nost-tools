AMQP Protocol
============

*A brief summary of the AMQP protocol with links to detailed resources and a list of useful terminology used throughout this documentation.*

AMQP as a Standard Messaging Protocol
------------------------------------

AMQP (Advanced Message Queuing Protocol) is an open standard application layer protocol for message-oriented middleware. It's designed for enterprise messaging with a focus on reliability, security, and interoperability between different systems. AMQP enables applications to send messages reliably between distributed systems, often in high-throughput, mission-critical applications. There are many resources that cover the details and benefits of using the AMQP protocol, including but not limited to:

  * `OASIS Standard AMQP Version 1.0 <https://docs.oasis-open.org/amqp/core/v1.0/os/amqp-core-overview-v1.0-os.html>`_
  
  * `AMQP.org <https://www.amqp.org>`_  
  
  * `Pika Python client library <https://pypi.org/project/pika/>`_ - (NOTE: This is one of many popular AMQP libraries)

|

Useful Terminology/Nomenclature
------------------------------

A deep understanding of the protocol is not necessary to start working with AMQP, but the following are some terms that will be used commonly to explain the NOS-T architecture:

  * broker: 
                A server that receives and routes messages. In AMQP, the broker manages exchanges, queues, and bindings. NOS-T is hosted on an Amazon Elastic Compute Cloud (EC2) instance.

  * client: 
                A device or application running an AMQP library and connecting to an AMQP broker over a network. These are typically applications that need reliable message delivery in enterprise environments.

  * connection: 
                A network connection between a client and broker, typically using TCP/IP. AMQP connections are persistent and designed to handle failures gracefully.

  * channel: 
                A virtual connection within a single AMQP connection. Multiple channels allow for multiple logical connections over a single TCP connection, improving efficiency.

  * exchange: 
                A routing mechanism that receives messages from publishers and routes them to queues based on routing keys and bindings. AMQP defines several exchange types (direct, topic, fanout, headers).
  
  * queue: 
                A buffer that stores messages. Consumers connect to queues to receive messages. Queues can be durable, temporary, exclusive, or auto-delete.

  * binding: 
                A rule that tells an exchange which queues to route messages to based on routing keys or header attributes.

  * publisher: 
                A client that sends a message to an exchange with a specific routing key.

  * consumer:
                A client that connects to a queue to receive messages.
                
  * message:
                The data transmitted through AMQP, consisting of a set of properties (including headers and routing information) and a binary payload.

|

Message Routing with Exchange Types
----------------------------------

AMQP provides sophisticated message routing through different exchange types that determine how messages are distributed to queues:

The most common exchange types are:

1. **Direct Exchange**: Routes messages to queues based on an exact match between the routing key and the binding key. This is useful for direct point-to-point communication.

2. **Topic Exchange**: Routes messages to queues based on pattern matching between the routing key and the binding pattern. This allows for more flexible subscriptions.

3. **Fanout Exchange**: Routes messages to all queues bound to the exchange, regardless of routing keys. This implements the broadcast pattern.

4. **Headers Exchange**: Routes messages based on header attributes rather than routing keys, allowing for more complex routing decisions.

Topic exchanges support pattern matching using wildcards:

* **'*'**: Matches exactly one word in the routing key
* **'#'**: Matches zero or more words in the routing key

For example, if using the convention {SERVICE}.{CATEGORY}.{ACTION}, a consumer could bind to:
* "service1.*.update" to receive all update actions for any category in service1
* "service1.#" to receive all messages for service1
* "*.critical.*" to receive all critical messages across all services

These routing capabilities allow for flexible and powerful message distribution patterns while maintaining control over message flow.

..
    other possible definitions to include: message durability, queue durability, acknowledgments, prefetch count