#!/usr/bin/env python
import json
import time
from datetime import datetime

import pika

# Connection parameters
credentials = pika.PlainCredentials("admin", "admin")
parameters = pika.ConnectionParameters("localhost", 5672, "/", credentials)

# Establish connection to RabbitMQ
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Declare an exchange
exchange_name = "nost_example"
channel.exchange_declare(exchange=exchange_name, exchange_type="topic")

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
            "data": f"Test message {message_count}",
        }

        routing_key = "nost.example.data"
        message_body = json.dumps(message)

        channel.basic_publish(
            exchange=exchange_name, routing_key=routing_key, body=message_body
        )

        print(f"Published message {message_count}: {message_body}")
        time.sleep(2)  # Publish a message every 2 seconds

except KeyboardInterrupt:
    print("Stopping publisher...")
finally:
    connection.close()
    print("Connection closed")
