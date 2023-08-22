# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 21:31:57 2023

@author: brian
"""

import paho.mqtt.client as mqtt
# import csv
import json
from datetime import datetime
from dotenv import dotenv_values

# initializing flood list
stateList = []


def on_message(mqttc, obj, msg):
    """ Callbacks to process incoming messages."""
    # callback for floodWarning
    if msg.topic in ["BCtest/satellite/state"]:
        dataIn = json.loads(msg.payload.decode("utf-8"))
        velocity=dataIn['velocity']
        latitude=dataIn['latitude']
        longitude=dataIn['longitude']
        attitude=dataIn['attitude']
        angular_velocity = dataIn['angular_velocity']
        target_quaternion=dataIn['target_quaternion']
        roll_angle = dataIn['roll_angle']
        error_angle=dataIn['error_angle']
        radius=dataIn['radius']
        commRange=dataIn['commRange']
        time=dataIn['time']
        
        stateDict = {"floodId":floodId, "siteName":siteName, "startTime":startTime}
        stateList.append(warningDict)
        
    