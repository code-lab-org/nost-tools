# -*- coding: utf-8 -*-
"""
This application publishes random "science events" for testing other NOS-T
applications. The message payload contains the current time, a random location,
and the science utility function value at that time step.
"""

import json
import time
from datetime import datetime, timedelta

import pika
from dotenv import dotenv_values
from numpy import random

if __name__ == "__main__":

    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # Connection parameters for RabbitMQ
    pika_credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    parameters = pika.ConnectionParameters(HOST, PORT, "/", pika_credentials)

    # Establish connection to RabbitMQ
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare an exchange
    exchange_name = "science_event"
    channel.exchange_declare(exchange=exchange_name, exchange_type="topic")

    try:
        while True:
            # event trigger
            eventRand = random.randint(100)
            if eventRand <= 99:  # the percent chance an event will occur

                # event location
                eventLat = random.uniform(-180, 180)
                eventLon = random.uniform(-90, 90)

                # loop for utility function
                for i in range(10):

                    # science utility function
                    utility = -((i / 10) ** 2) + 1
                    currentTime = datetime.now()
                    currentTime = currentTime.strftime("%H:%M:%S")

                    # publish event utility message
                    eventMessage = {
                        "time": currentTime,
                        "latitude": eventLat,
                        "longitude": eventLon,
                        "utility": utility,
                    }

                    routing_key = "BCtest.AIAA.eventUtility"
                    message_body = json.dumps(eventMessage)
                    channel.basic_publish(
                        exchange=exchange_name,
                        routing_key=routing_key,
                        body=message_body,
                    )
                    print(eventMessage)

                    # wait for next utility step
                    time.sleep(1)

            # time step between possible events
            next_step = datetime.now() + timedelta(seconds=5)

            # allows application to be stopped with GUI every second
            while datetime.now() < next_step:
                time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping publisher...")
    finally:
        connection.close()
        print("Connection closed")
