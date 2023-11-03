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

    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]
    # build the MQTT client
    client = mqtt.Client()
    # set tls certificate
    client.tls_set()
    # connect to MQTT server on port 8883
    client.connect("testbed.mysmce.com", 8883)
    # start a background thread to let MQTT do things
    client.loop_start()

    while True:
        
        # event trigger
        eventRand = random.randint(100)
        if eventRand <= 99:  # the percent chance an event will occur
            
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
        next_step = datetime.now() + timedelta(seconds=5)

        # allows application to be stopped with GUI every second
        while datetime.now() < next_step:
           time.sleep(1)


