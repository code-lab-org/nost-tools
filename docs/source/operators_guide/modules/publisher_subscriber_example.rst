.. _publisher_subscriber_example:

Creating a Simple Publisher-Subscriber Example
=============================================

After setting up your RabbitMQ broker, you can test its functionality by creating a simple publisher-subscriber system. This example demonstrates how messages flow through the broker from publishers to subscribers.

Prerequisites
------------

* NOS-T tools installed (as described in :ref:`_installation`.)
* RabbitMQ broker running (as described in :ref:`localBroker`.)
* Python 3.6+ installed
* Basic understanding of messaging concepts

Installing Required Libraries
----------------------------

First, install the Python client library for RabbitMQ:

.. code-block:: console

    >>> pip install pika

Creating a Publisher
-------------------

Create a file named ``publisher.py`` with the following content:

.. code-block:: python

    #!/usr/bin/env python
    import pika
    import time
    import json
    from datetime import datetime

    # Connection parameters
    credentials = pika.PlainCredentials('admin', 'admin')
    parameters = pika.ConnectionParameters('localhost',
                                          5672,
                                          '/',
                                          credentials)

    # Establish connection to RabbitMQ
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare an exchange
    exchange_name = 'nost_example'
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

    # Publish messages
    try:
        message_count = 0
        print("Starting to publish messages. Press CTRL+C to stop.")
        
        while True:
            message_count += 1
            timestamp = datetime.now().isoformat()
            
            message = {
                "sequence": message_count,
                "timestamp": timestamp,
                "data": f"Test message {message_count}"
            }
            
            routing_key = 'nost.example.data'
            message_body = json.dumps(message)
            
            channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=message_body
            )
            
            print(f"Published message {message_count}: {message_body}")
            time.sleep(2)  # Publish a message every 2 seconds
            
    except KeyboardInterrupt:
        print("Stopping publisher...")
    finally:
        connection.close()
        print("Connection closed")

Creating a Subscriber
--------------------

Create a file named ``subscriber.py`` with the following content:

.. code-block:: python

    #!/usr/bin/env python
    import pika
    import json

    # Connection parameters
    credentials = pika.PlainCredentials('admin', 'admin')
    parameters = pika.ConnectionParameters('localhost',
                                          5672,
                                          '/',
                                          credentials)

    # Establish connection to RabbitMQ
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare the same exchange as the publisher
    exchange_name = 'nost_example'
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

    # Create a queue with a random name
    result = channel.queue_declare('', exclusive=True)
    queue_name = result.method.queue

    # Bind the queue to the exchange with a routing key
    binding_key = 'nost.example.*'
    channel.queue_bind(
        exchange=exchange_name,
        queue=queue_name,
        routing_key=binding_key
    )

    print(f"Subscribed to {exchange_name} with binding key {binding_key}")
    print("Waiting for messages. To exit press CTRL+C")

    # Define a callback function to be called when a message is received
    def callback(ch, method, properties, body):
        try:
            message = json.loads(body)
            print(f"Received message {message['sequence']}: {message['data']} (sent at {message['timestamp']})")
        except json.JSONDecodeError:
            print(f"Received message (non-JSON): {body}")

    # Set up the consumer
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=True
    )

    # Start consuming messages
    channel.start_consuming()

Running the Example
------------------

1. Open two terminal windows.
2. In the first terminal, start the subscriber:

   .. code-block:: console

       >>> python subscriber.py
       Subscribed to nost_example with binding key nost.example.*
       Waiting for messages. To exit press CTRL+C

3. In the second terminal, start the publisher:

   .. code-block:: console

       >>> python publisher.py
       Starting to publish messages. Press CTRL+C to stop.
       Published message 1: {"sequence": 1, "timestamp": "2023-06-02T12:34:56.789012", "data": "Test message 1"}
       Published message 2: {"sequence": 2, "timestamp": "2023-06-02T12:34:58.789012", "data": "Test message 2"}
       ...

4. Observe the messages being received in the subscriber terminal:

   .. code-block:: console

       Received message 1: Test message 1 (sent at 2023-06-02T12:34:56.789012)
       Received message 2: Test message 2 (sent at 2023-06-02T12:34:58.789012)
       ...

Understanding the Example
------------------------

This example demonstrates the core concepts of messaging with RabbitMQ:

1. **Publishers** send messages to an exchange with a specific routing key.
2. **Exchanges** route messages to queues based on the routing key and exchange type.
3. **Queues** hold messages until they are consumed.
4. **Subscribers** consume messages from queues.

The publisher creates messages with a sequence number and timestamp, then publishes them to the "nost_example" exchange with the routing key "nost.example.data".

The subscriber creates a queue, binds it to the exchange with the binding pattern "nost.example.*", and then consumes messages that match this pattern.

Troubleshooting
--------------

If you encounter issues:

1. **Connection refused**: Ensure your RabbitMQ broker is running. Check with ``docker ps``.
2. **Authentication failed**: Verify the username and password in the code match your RabbitMQ configuration.
3. **No messages received**: Check that the exchange name and routing/binding keys match between publisher and subscriber.
4. **Broker not responding**: Restart the RabbitMQ container using ``docker restart rabbitmq``.

You can also check the RabbitMQ management interface at http://localhost:15672/ to view exchanges, queues, and message flows.

Next Steps
---------

- Try modifying the routing keys to see how message routing changes.
- Experiment with different exchange types (direct, fanout, headers).
- Create multiple subscribers with different binding patterns.
- Add message persistence for reliability.