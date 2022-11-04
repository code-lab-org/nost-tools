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
from dotenv import dotenv_values

def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    # setting up DataFrame
    dataIn = json.loads(msg.payload.decode("utf-8"))
    requestTime = dataIn["requestTime"]["value"]
    siteName = dataIn['siteName']
    dataTime = dataIn['dataTime']
    gageHeight = dataIn['gageHeight']
    latitude = dataIn['latitude']
    longitude = dataIn['longitude']

    # writing .csv for dashboard
    with open(filename, 'a') as csvfile:
        for entry in range(len(siteName)):
            dataOut = [siteName[entry],requestTime,dataTime[entry],gageHeight[entry],latitude[entry],longitude[entry]]
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(dataOut)

# name guard
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

    # field names
    fields = ['Site_Name','Request_Time','Data_Time','Gage_Height','Latitude','Longitude']
    # name of output file
    filename = "gage_height_for_viz.csv"
    with open(filename, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)
        # writing the fields
        csvwriter.writerow(fields)


    # subscribe to flow rate topic
    client.subscribe("BCtest/streamGauge/gageHeight",0)


    # bind the message handler
    client.on_message = on_message
    # start a background thread to let MQTT do things
    client.loop_forever()
