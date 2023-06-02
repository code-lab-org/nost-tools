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
    dcm_target = np.array([[ 0.707107, -0, -0.707107],
                           [0, 1, -0],
                           [0.707107, 0, 0.707107]])
    
    dcm_target = dcm_target.tolist()
    
    w_nominal = [0,0,0.0011313759174069189]

    # q = np.array([-0.01731244,  0.38229163, -0.04179593, 0.92293363])
    
    # 25 deg rotation about y
    #q = np.array([0 , 0.21643961, 0 , 0.97629601])


    while True:
        
        # publish event utility message
        heartbeat = {"t":t,
                     "i":i,
                     "DCM_target":dcm_target,
                     "w_nominal":w_nominal}
        client.publish("BCtest/ADCS/heartbeat", payload=json.dumps(heartbeat))
        print(heartbeat)

        # #wait for next utility step
        # time.sleep(.01)

        # time step between heartbeats

        # if t == 200:
            # q_target = quaternion_multiply(
            #     np.array(
            #         [0, np.sin(45 * np.pi / 180 / 2), 0,
            #           np.cos(45 * np.pi / 180 / 2)]), q)
            # q_target = np.array([0 , 0.21643961, 0 , 0.97629601])
            
            # # q target with q multiplication
            # #q_target = np.array([-8.77668000e-07, -8.90474461e-02, -9.92038819e-01, -8.90474068e-02])
            
            # dcm_target = quaternion_to_dcm(q_target)
            # dcm_target = dcm_target.tolist()
            # w_nominal = [-0.000386953, 0, -0.00106315]

            # compute the nominal angular velocity required to achieve the reference
            # attitude; first in inertial coordinates then body
            # w_nominal_i = 2 * np.pi / period * normalize(cross(r_0, v_0))
            # w_nominal = np.matmul(dcm_0_nominal, w_nominal_i)
            
        #next_step = datetime.now() + timedelta(seconds=.5)
        t += 1
        i += 1
        
        if t == 1001:
            break

        # allows application to be stopped with GUI every second
        #while datetime.now() < next_step:
        time.sleep(.005)
