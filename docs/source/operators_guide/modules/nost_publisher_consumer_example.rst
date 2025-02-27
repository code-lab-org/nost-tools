.. _nost_publisher_consumer_example:

Creating a NOST Tools Publisher-Consumer Example
===============================================

This example demonstrates how to create a simple publisher-consumer system using the NOST Tools library. The example showcases how messages flow through the broker from publishers to consumers using the NOST Tools' abstractions.

Prerequisites
------------

* NOS-T tools installed (as described in :ref:`installation`).
* RabbitMQ broker running (as described in :ref:`localBroker`).
* Basic understanding of NOST messaging concepts.

Configuration File
-----------------

First, create a file named ``sos.yaml`` with the following content:

.. code-block:: yaml

    info:
      title: Novel Observing Strategies Testbed (NOS-T) YAML Configuration
      version: '1.0.0'
      description: Version-controlled AsyncAPI document for RabbitMQ event broker with Keycloak authentication within NOS-T
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
      keycloak:
        host: "nost.smce.nasa.gov"
        port: 8443
        tls: True
        token_refresh_interval: 10 #in seconds
        realm: "NOS-T"
    execution:
      general:
        prefix: sos
      manager:
        sim_start_time: "2019-03-01T23:59:59+00:00"
        sim_stop_time: "2019-03-10T23:59:59+00:00"
        start_time:
        time_step: "0:00:01"
        time_scale_factor: 288 # 1 simulation day = 5 wallclock minutes
        time_scale_updates: []
        time_status_step: "0:00:01" # 1 second * time scale factor
        time_status_init: "2019-03-01T23:59:59+00:00"
        command_lead: "0:00:05"
        required_apps:
          - manager
          - planner
          - appender
          - simulator
        init_retry_delay_s: 5
        init_max_retry: 5
        set_offset: True
        shut_down_when_terminated: False
      managed_application:
        time_scale_factor: 288 # 1 simulation day = 5 wallclock minutes
        time_step: "0:00:01" # 1 second * time scale factor 
        set_offset: True
        time_status_step: "0:00:10" # 10 seconds * time scale factor
        time_status_init: "2019-03-01T00:00:00+00:00"
        shut_down_when_terminated: False
        manager_app_name: "manager"

Creating a Publisher
-------------------

Create a file named ``nost_publisher.py`` with the following content:

.. code-block:: python

    from nost_tools.config import ConnectionConfig
    from nost_tools.managed_application import ManagedApplication
    import time
    import logging
    import random

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    # Load connection configuration from YAML
    config = ConnectionConfig(yaml_file="sos.yaml")

    # Define application name
    NAME = "publisher"

    # Create the managed application
    app = ManagedApplication(NAME)

    # Start up the application
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config
    )

    # Send messages in a loop
    try:
        message_count = 0
        logger.info("Starting to publish messages. Press CTRL+C to stop.")
        
        while True:
            message_count += 1
            message = f"This is test message #{message_count} with value: {random.random():.4f}"
            
            # Send a message
            app.send_message(
                app_name="publisher",
                app_topics="test",
                payload=message
            )
            
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

    from nost_tools.config import ConnectionConfig
    from nost_tools.managed_application import ManagedApplication
    import logging
    import time

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    def callback(ch, method, properties, body):
        """Process received messages"""
        body = body.decode("utf-8")
        logger.info(f"Received message: {body}")

    # Load connection configuration from YAML
    config = ConnectionConfig(yaml_file="sos.yaml")

    # Define application name
    NAME = "observer1"

    # Create the managed application
    app = ManagedApplication(NAME)

    # Start up the application
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config
    )

    # Register callback for messages from publisher
    app.add_message_callback(
        app_name="publisher",
        app_topic="test",
        user_callback=callback
    )

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

Understanding the NOST Tools Implementation
-----------------------------------------

This example demonstrates several key NOST Tools concepts:

1. **Connection Configuration**: The ``ConnectionConfig`` class loads broker settings from a YAML file.
2. **Managed Application**: The ``ManagedApplication`` class handles connection management and message routing.
3. **Message Callbacks**: The consumer registers callbacks that are triggered when messages arrive.
4. **Topics**: Messages are published with specific topics that consumers can subscribe to.
5. **Payload Handling**: Messages can carry arbitrary string payloads.

Unlike the direct pika implementation, NOST Tools abstracts away many messaging details, making the code more concise and focused on the application logic.

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
- Explore other NOST Tools features like time synchronization and simulation control