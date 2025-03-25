#!/usr/bin/env python
import json

import pika

# Connection parameters
credentials = pika.PlainCredentials("admin", "admin")
parameters = pika.ConnectionParameters("localhost", 5672, "/", credentials)

# Establish connection to RabbitMQ
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Declare the same exchange as the publisher
exchange_name = "nost_example"
channel.exchange_declare(exchange=exchange_name, exchange_type="topic")

# Create a queue with a random name
result = channel.queue_declare("", exclusive=True)
queue_name = result.method.queue

# Bind the queue to the exchange with a routing key
binding_key = "nost.example.*"
channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=binding_key)

print(f"Subscribed to {exchange_name} with binding key {binding_key}")
print("Waiting for messages. To exit press CTRL+C")


# Define a callback function to be called when a message is received
def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        print(
            f"Received message {message['sequence']}: {message['data']} (sent at {message['timestamp']})"
        )
    except json.JSONDecodeError:
        print(f"Received message (non-JSON): {body}")


# Set up the consumer
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

# Start consuming messages
channel.start_consuming()
