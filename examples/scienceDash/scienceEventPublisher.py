# -*- coding: utf-8 -*-
"""
This application publishes random "science events" for testing other NOS-T
applications. The message payload contains the current time, a random location,
and the science utility function value at that time step.
"""

import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime, timedelta
from numpy import random
from dotenv import dotenv_values

if __name__ == "__main__":

    # setting credentials from .env file
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]
    # build the MQTT client
    client = mqtt.Client()
    # set client username and password
    client.username_pw_set(username=USERNAME, password=PASSWORD)
    # set tls certificate
    client.tls_set()
    # connect to MQTT server
    client.connect(HOST, PORT)
    # start a background thread to let MQTT do things
    client.loop_start()

    while True:

        # event trigger
        eventRand = random.randint(100)
        if eventRand <= 99:

            # event location
            eventLat = random.uniform(-180,180)
            eventLon = random.uniform(-90,90)

            # loop for utility function
            for i in range(10):

                # science utility funciton
                utility = -((i/10)**2)+1
                currentTime = datetime.now()
                currentTime = currentTime.strftime('%H:%M:%S')

                # publish event utility message
                eventMessage = {"time":currentTime,
                                "latitude":eventLat,
                                "longitude":eventLon,
                                "utility":utility}
                client.publish("BCtest/AIAA/eventUtility", payload=json.dumps(eventMessage))
                print(eventMessage)

                #wait for next utility step
                time.sleep(1)

        # time step between possible events
        next_step = datetime.now() + timedelta(seconds=1)

        # allows application to be stopped with GUI every second
        while datetime.now() < next_step:
           time.sleep(1)
