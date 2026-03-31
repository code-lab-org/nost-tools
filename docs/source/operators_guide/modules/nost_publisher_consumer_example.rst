.. _nost_publisher_consumer_example:

Creating a NOS-T Publisher-Consumer Example
===============================================

This example demonstrates how to create a simple publisher-consumer system using the NOS-T library. The example showcases how messages flow through the broker from publishers to consumers using NOS-T.

Prerequisites
------------

* NOS-T installed (as described in :ref:`installation`).
* RabbitMQ broker running (as described in :ref:`localBroker`).
* Basic understanding of NOS-T messaging concepts.

Configuration File
-----------------

First, create a file named ``sos.yaml`` with the following content:

.. code-block:: yaml

  info:
    title: Novel Observing Strategies Testbed (NOS-T) YAML Configuration
    version: '1.0.0'
    description: Version-controlled AsyncAPI document for RabbitMQ event broker
  servers:
    rabbitmq:
      keycloak_authentication: False
      host: "localhost"
      port: 5672
      tls: False
      virtual_host: "/"
      message_expiration: "60000" # in milliseconds, message expiration time
      delivery_mode: 2 # 1=transient, 2=durable
      content_type: "text/plain"
      heartbeat: 30 # in seconds
      connection_attempts: 3
      retry_delay: 5 # in seconds
  execution:
    general:
      prefix: sos

Then, create a ``.env`` file with the following content. The required environment variables depend on your authentication mode (see :ref:`authModes` for details):

.. code-block:: bash

    # Basic Auth (localhost development) - username and password only
    USERNAME="admin"
    PASSWORD="admin"

    # Keycloak User Account - add these for Keycloak authentication
    # CLIENT_ID="your-client-id"
    # CLIENT_SECRET_KEY="your-client-secret"

    # Keycloak Service Account - client credentials only (no username/password)
    # CLIENT_ID="your-client-id"
    # CLIENT_SECRET_KEY="your-client-secret"

Creating a Publisher
-------------------

Create a file named ``nost_publisher.py`` with the following content:

.. code-block:: python

    import logging
    import random
    import time

    from nost_tools.application import Application
    from nost_tools.configuration import ConnectionConfig

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    # Load connection configuration from YAML
    config = ConnectionConfig(yaml_file="sos.yaml")

    # Define application name
    NAME = "publisher"

    # Create the managed application
    app = Application(NAME)

    # Start up the application
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix, config
    )

    # Send messages in a loop
    try:
        message_count = 0
        logger.info("Starting to publish messages. Press CTRL+C to stop.")

        while True:
            message_count += 1
            message = (
                f"This is test message #{message_count} with value: {random.random():.4f}"
            )

            # Send a message
            app.send_message(app_name=NAME, app_topics="test", payload=message)

            logger.info(f"Published message: {message}")
            time.sleep(2)  # Publish a message every 2 seconds

    except KeyboardInterrupt:
        logger.info("Stopping publisher...")
    finally:
        # Clean shutdown would go here
        logger.info("Publisher stopped")


Creating a Consumer
--------------------

Create a file named ``nost_consumer.py`` with the following content:

.. code-block:: python

    import logging
    import time

    from nost_tools.application import Application
    from nost_tools.configuration import ConnectionConfig

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()


    def callback(ch, method, properties, body):
        """Process received messages"""
        body = body.decode("utf-8")
        logger.info(f"Received message: {body}")


    # Load connection configuration from YAML
    config = ConnectionConfig(yaml_file="sos.yaml")

    # Define application name
    NAME = "consumer"

    # Create the managed application
    app = Application(NAME)

    # Start up the application
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix, config
    )

    # Register callback for messages from publisher
    app.add_message_callback(app_name="publisher", app_topic="test", user_callback=callback)

    logger.info("Consumer started. Waiting for messages. Press CTRL+C to stop.")

    try:
        # Keep application running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Consumer stopped")

Running the Example
------------------

1. First, make sure you have RabbitMQ running (as described in the :ref:`localBroker` guide).
2. Open two terminal windows.
3. In the first terminal, start the consumer:

   .. code-block:: console

       python3 nost_consumer.py

4. In the second terminal, start the publisher:

   .. code-block:: console

       python3 nost_publisher.py

5. Observe the messages being received in the consumer terminal.

Understanding the NOS-T Implementation
-----------------------------------------

This example demonstrates several key NOS-T concepts:

1. **Connection Configuration**: The ``ConnectionConfig`` class loads broker settings from a YAML file.
2. **Managed Application**: The ``ManagedApplication`` class handles connection management and message routing.
3. **Message Callbacks**: The consumer registers callbacks that are triggered when messages arrive.
4. **Topics**: Messages are published with specific topics that consumers can subscribe to.
5. **Payload Handling**: Messages can carry arbitrary string payloads.

Unlike the direct pika implementation, NOS-T abstracts away many messaging details, making the code more concise and focused on the application logic.

Troubleshooting
--------------

If you encounter issues:

1. **Configuration errors**: Ensure your ``sos.yaml`` file is correctly formatted and contains valid broker details.
2. **Connection refused**: Ensure your RabbitMQ broker is running. Check with ``docker ps``.
3. **Authentication failed**: Verify the username and password in the YAML file match your RabbitMQ configuration.
4. **No messages received**: Check that the application names and topics match between publisher and consumer.

You can also check the RabbitMQ management interface at http://localhost:15672/ to view exchanges, queues, and message flows.

Next Steps
---------

- Try adding multiple consumers with different callbacks
- Experiment with different message payloads (JSON, XML, etc.)
- Implement more complex routing patterns using different topics
- Explore other NOS-T features like time synchronization and simulation control