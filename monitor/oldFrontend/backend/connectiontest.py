import json
import time
from datetime import datetime, timedelta, timezone

import ntplib
import paho.mqtt.client as mqtt
from flask import Flask, request, send_from_directory
from nost import (HOST, PASSWORD, PORT, USERNAME, Middleware, Mode, Simulator,
                  get_wallclock_offset, init, start, stop, test_script, update)

def send_alternating_messages(topic1, topic2, duration):
    # Create the MQTT client
    client = mqtt.Client()

    # Set client username and password
    client.username_pw_set(username=USERNAME, password=PASSWORD)

    # Set TLS certificate
    client.tls_set()

    # Define the on_connect and on_message functions
    def on_connect(client, userdata, flags, rc):
        print(f"Connected to MQTT server with result code: {rc}")
        client.subscribe(topic1)
        client.subscribe(topic2)
        print(f"Subscribed to the following topics: {topic1}, {topic2}")

    def on_message(client, userdata, msg):
        if msg.topic == topic1:
            print(f"Received message from {topic1}: {msg.payload.decode('utf-8')}")
        elif msg.topic == topic2:
            print(f"Received message from {topic2}: {msg.payload.decode('utf-8')}")
        else:
            print(f"Received message on an unexpected topic: {msg.topic}")

    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT server on the specified host and port
    client.connect(HOST, PORT)

    # Start the MQTT client loop
    client.loop_start()

    start_time = time.time()
    count = 1
    while time.time() - start_time <= duration:
        # Decide which topic to use based on the count
        if count % 2 == 1:
            topic = topic1
        else:
            topic = topic2

        # Publish a test message to the MQTT server with count
        message = f"This is message number {count} for {topic}"
        client.publish(topic, message)
        print(f"Test message {count} sent: {message}")

        # Increment the count
        count += 1

        # Wait for 1 second before sending the next message
        time.sleep(1)

    # Close the connection to the MQTT server
    client.disconnect()
    client.loop_stop()

# Set the duration for sending messages (in seconds)
duration = 100000  # Change this to the desired duration for each run

# Topics for alternating messages
TPC1 = "test/mama"
TPC2 = "test/papa"

# Send alternating messages between TPC1 and TPC2
send_alternating_messages(TPC1, TPC2, duration)
