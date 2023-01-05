# -*- coding: utf-8 -*-
"""
This application uses the python requests library to get real-time stream
gauge data from the USGS National Water Information Service (NWIS). NWIS
regularly publishes this information online. The NWIS information is
periodically checked and once data is received. Then, the data is parsed
and converted into a JSON message containing the request time and flow rate
data/flow rate update time for site.  Finally, it is published to the NOS-T
system, currently using the BCtest/streamGauge/gageHeight topic.
The following link can be used to set up different NWIS data requests, i.e.
different locations and/or different outputs:
https://waterservices.usgs.gov/rest/IV-Test-Tool.html
"""

import paho.mqtt.client as mqtt
import time
import json
import requests
from datetime import datetime, timedelta
import pandas as pd
from numpy import random
from dotenv import dotenv_values
# import csv
# from nost_tools.application_utils import ConnectionConfig, ShutDownObserver

# initialize dicts
siteName = {}
dataTime = {}
gageHeight = {}
location = {}
latitude = {}
longitude = {}
floodId = 0



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

        # getting stream gauge ID numbers from .csv file and making request url
        df = pd.read_csv("siteNumbers.csv")
        siteIds = ",".join([f"{site:08}"for site in df.Site])
        urlBegin = "https://waterservices.usgs.gov/nwis/iv/?format=json&indent=on&sites="
        urlEnd = "&parameterCd=00065&siteStatus=all"
        requestUrl = urlBegin+siteIds+urlEnd


        # web request to NWIS
        rawResponse = requests.get(requestUrl)
        response = rawResponse.json()

        # NWIS outputs
        requestTime = response['value']['queryInfo']['note'][3]#['value']
        for i, timeSeries in enumerate(response['value']['timeSeries']):
            siteName[i] = timeSeries['sourceInfo']['siteName']
            dataTime[i] = timeSeries['values'][0]['value'][0]['dateTime']
            gageHeight[i] = float(timeSeries['values'][0]['value'][0]['value'])
            latitude[i] = float(timeSeries['sourceInfo']['geoLocation']['geogLocation']['latitude'])
            longitude[i] = float(timeSeries['sourceInfo']['geoLocation']['geogLocation']['longitude'])
        # gaugeList = [siteName, dataTime, gageHeight, latitude, longitude]

        # flood trigger
        floodRand = random.randint(100)
        locationRand = random.randint(len(response['value']['timeSeries']))
        if floodRand <= 50:   # percent chance of flood
            gageHeight[locationRand] = gageHeight[locationRand]+10.0

            # publish flood warning
            floodWarningMessage = {
                'siteName':siteName[locationRand],
                'floodId':floodId,
                'startTime':str(datetime.now()),#response['value']['queryInfo']['note'][3]['value'],
                'latitude':latitude[locationRand],
                'longitude':longitude[locationRand]
                }
            floodId = floodId+1
            client.publish("BCtest/streamGauge/floodWarning", payload=json.dumps(floodWarningMessage))
            #print(floodWarningMessage)
            if floodId > 33:
                break

        # advance to next time step
        next_step = datetime.now() + timedelta(seconds=3)

        # outputs into message
        gageHeightMessage = {
            "requestTime":requestTime,
            "siteName":list(siteName.values()),
            "dataTime":list(dataTime.values()),
            "gageHeight":list(gageHeight.values()),
            "latitude":list(latitude.values()),
            "longitude":list(longitude.values())
            }

        # publish time and gage height
        client.publish("BCtest/streamGauge/gageHeight", payload=json.dumps(gageHeightMessage))
        print(gageHeightMessage)

        # allows application to be stopped with GUI every second
        while datetime.now() < next_step:
           time.sleep(1)
