# -*- coding: utf-8 -*-
"""
    *An application that aggregates data from the floods application case to determine latency metrics*

    This application subscribes to the timestamps published to the flood warning, image taken, and image downlinked ats. The data are saved in the list, floodList.
"""

import paho.mqtt.client as mqtt
# import csv
import json
from datetime import datetime
from dotenv import dotenv_values

# initializing flood list
floodList = []


def on_message(mqttc, obj, msg):
    """ Callbacks to process incoming messages."""
    # callback for floodWarning
    if msg.topic in ["BCtest/streamGauge/floodWarning"]:
        dataIn = json.loads(msg.payload.decode("utf-8"))
        floodId = dataIn['floodId']
        siteName = dataIn['siteName']
        startTime = datetime.strptime(dataIn['startTime'],"%Y-%m-%d %H:%M:%S.%f")
        #warningDict = [{"floodId":[floodId]}, {"siteName":[siteName]}, {"startTime":[startTime]}]
        warningDict = {"floodId":floodId, "siteName":siteName, "startTime":startTime}
        floodList.append(warningDict)

    # callback for flood imaged
    if msg.topic in ["BCtest/constellation/imageTaken"]:
        dataIn = json.loads(msg.payload.decode("utf-8"))
        floodId = dataIn["floodId"]
        imageTime = dataIn["imaged"]
        imageBy = dataIn["imagedBy"]
        floodList[floodId]["imageTime"]=datetime.strptime(imageTime,"%Y-%m-%dT%H:%M:%S.%f")
        floodList[floodId]["imagedBy"]=imageBy

    # callback for image downlinked
    if msg.topic in ["BCtest/constellation/imageDownlinked"]:
        dataIn = json.loads(msg.payload.decode("utf-8"))
        floodId = dataIn["floodId"]
        downlinkTime = dataIn["downlinked"]
        downlinkBy = dataIn["downlinkedBy"]
        floodList[floodId]["downlinkTime"]=datetime.strptime(downlinkTime,"%Y-%m-%dT%H:%M:%S.%f")
        floodList[floodId]["downlinkedBy"]=downlinkBy
        latency = floodList[floodId]["downlinkTime"]-floodList[floodId]["startTime"]
        floodList[floodId]["latency"] = latency.total_seconds()
        print(floodId)

        # import pandas as pd
        # df = pd.DataFrame(floodList)
        # df.to_csv("testdata1_sval.csv")

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


    # subscribe to topics
    client.subscribe("BCtest/streamGauge/floodWarning",0)
    client.subscribe("BCtest/constellation/imageTaken",0)
    client.subscribe("BCtest/constellation/imageDownlinked",0)

    # bind the message handler
    client.on_message = on_message
    # start a background thread to let MQTT do things
    client.loop_forever()
