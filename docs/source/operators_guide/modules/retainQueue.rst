Configuring a Solace Broker for Message Queueing
================================================

Although the MQTT protocol was not originally designed for message queueing, Solace Event Brokers are equipped to handle persistent sessions and queues on topic endpoints. Asynchronous queueing is possible with NOS-T, but it is more consistent when topic endpoints are mapped to the queues directly on the Solace Broker.

Quality of Service
------------------

The 

In previous section, we will stay with a simple fire and forget (QOS = 0) architecture. This section gets into the nuance of QOS, retained messages, and persistent clients. Walks through how to set this up in Solace.

Need queueing enabled on broker and to allot memory for it (recommended size of memory based on use case).

Two ways to create a queue: 1) Created by Management API (better, more control for operator to clear out queues), or 2) Created by publisher by setting retain = true and increasing the QOS from 0 to 1.

Discuss Consuming of Retained Messages (necessary because a Queue can get backed up, don't need to retain all messages if everyone who was supposed to received it).

Explain what a persistent client is (clean_start = "False") and how the broker remembers the subscriptions of the client AFTER it has disconnected (requires specifying a Client_ID). This allows the client to receive any queued messages when next it connects to the broker.

