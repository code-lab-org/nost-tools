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
import numpy as np
from dotenv import dotenv_values
from math_utils import (quaternion_multiply,
                        dcm_to_quaternion, quaternion_to_dcm, normalize, cross)


if __name__ == "__main__":

    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]
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
    
    # for message
    t = 0
    i = 0
    dcm_target = [[ 0.707107, -0, -0.707107],
                  [0, 1, -0],
                  [0.707107, 0, 0.707107]]
    q = np.array([-0.01731244,  0.38229163, -0.04179593, 0.92293363])


    while True:

        # publish event utility message
        heartbeat = {"t":t,
                     "i":i,
                     "dcm_target":dcm_target}
        client.publish("BCtest/ADCS/heartbeat", payload=json.dumps(heartbeat))
        print(heartbeat)

        # #wait for next utility step
        # time.sleep(.01)

        # time step between heartbeats

        if t == 3000:
            q_target = quaternion_multiply(
                np.array(
                    [0, np.sin(45 * np.pi / 180 / 2), 0,
                      np.cos(45 * np.pi / 180 / 2)]), q)
            dcm_target = quaternion_to_dcm(q_target)
            dcm_target = dcm_target.tolist()
        #next_step = datetime.now() + timedelta(seconds=.5)
        t += 1
        i += 1
        
        if t == 6001:
            break

        # allows application to be stopped with GUI every second
        #while datetime.now() < next_step:
        time.sleep(.01)
