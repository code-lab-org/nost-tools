# -*- coding: utf-8 -*-
"""
    This application subscribes to the *userPrefix/streamGauge/flowrate* topic and
    uses a callback function to collect the time and flow rate data every time
    stream_gauge.py publishes. This data is then saved to a .csv file for the
    stream_dashboard.py application.
"""
from dotenv import dotenv_values
import paho.mqtt.client as mqtt
import csv
import json

def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    # setting up DataFrame for plot
    datain = json.loads(msg.payload.decode("utf-8"))
    requestTime = datain["properties"]["Request_time"]["value"]
    # Memphis, TN
    BPTime = datain["properties"]["Location"]["Memphis, TN"]["Time"]
    BPflowRate = float(datain["properties"]["Location"]["Memphis, TN"]["Flow_Rate"])
    datainBP = ['Memphis, TN',requestTime,BPTime,BPflowRate]
    # Baton Rouge, LA
    HSTime = datain["properties"]["Location"]["Baton Rouge, LA"]["Time"]
    HSflowRate = float(datain["properties"]["Location"]["Baton Rouge, LA"]["Flow_Rate"])
    datainHS = ['Baton Rouge, LA',requestTime,HSTime,HSflowRate]


    with open(filename, 'a') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(datainBP)
        csvwriter.writerow(datainHS)

# name guard
if __name__ == "__main__":

    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]

    # build the MQTT client
    client = mqtt.Client()
    # set client username and password (Note that these are placeholder variables, where variable type indicated with camel case)
    client.username_pw_set(username=USERNAME, password=PASSWORD)
    # set tls certificate
    client.tls_set()
    # connect to MQTT server on dedicated port (Note that these are placeholder variables, where variable type indicated with camel case)
    client.connect(HOST, PORT)

    # field names
    fields = ['Location','Request_Time','Data_Time','Flow_Rate']
    # name of output file
    filename = "flow_rate_for_viz.csv"
    with open(filename, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)
        # writing the fields
        csvwriter.writerow(fields)


    # subscribe to flow rate topic
    client.subscribe("userPrefix/streamGauge/flowRate",0)


    # bind the message handler
    client.on_message = on_message
    # start a background thread to let MQTT do things
    client.loop_forever()
