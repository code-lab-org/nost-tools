# -*- coding: utf-8 -*-
"""
    *An application that gets stream data and publishes it to NOS-T.*

    This application subscribes to the *BCtest/streamGauge/flowrate* topic and
    uses a callback function to collect the time and flow rate data every time
    stream_gauge.py publishes. This data is then saved to a .csv file for the
    stream_dashboard.py application.
"""

import paho.mqtt.client as mqtt
import csv
import json

def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    # setting up DataFrame 
    eventMessage = json.loads(msg.payload.decode("utf-8"))
    time = eventMessage["time"]
    latitude = eventMessage["latitude"]
    longitude = eventMessage["longitude"]
    utility = eventMessage["utility"]
    
    
    # writing .csv for dashboard
    with open(filename, 'a') as csvfile:
        dataOut = [eventMessage["time"],eventMessage["latitude"],eventMessage["longitude"],eventMessage["utility"]]
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(dataOut)

# name guard
if __name__ == "__main__":

    # build the MQTT client
    client = mqtt.Client()
    # set client username and password
    client.username_pw_set(username="bchell", password="cT8T1pd62KnZ")
    # set tls certificate
    client.tls_set()
    # connect to MQTT server on port 8883
    client.connect("testbed.mysmce.com", 8883)

    # field names
    fields = ["time","latitude","longitude","utility"]
    # name of output file
    filename = "scienceUtility.csv"
    with open(filename, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)
        # writing the fields
        csvwriter.writerow(fields)


    # subscribe to flow rate topic
    client.subscribe("BCtest/AIAA/eventUtility",0)


    # bind the message handler
    client.on_message = on_message
    # start a background thread to let MQTT do things
    client.loop_forever()
