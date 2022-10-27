# -*- coding: utf-8 -*-
"""
This application uses the python requests library to get real-time stream
gauge data from the USGS National Water Information Service (NWIS). NWIS
regularly publishes this information online. The NWIS information is
periodically checked and once data is received. Then, the data is parsed
and converted into a JSON message containing the request time and flow rate
data/flow rate update time for site.  Finally, it is published to the NOS-T
system, currently using the userPrefix/streamGauge/flowrate topic.
The following link can be used to set up different NWIS data requests, i.e.
different locations and/or different outputs:

https://waterservices.usgs.gov/rest/IV-Test-Tool.html
"""
from dotenv import dotenv_values
import paho.mqtt.client as mqtt
import time
import json
import requests
from datetime import datetime, timedelta
# from nost_tools.application_utils import ConnectionConfig, ShutDownObserver

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
    # start a background thread to let MQTT do things
    client.loop_start()

    while True:
        # get data points from Mississippi stream gauges in BP & Hastings, MN
        # rawresponse = requests.get("https://waterservices.usgs.gov/nwis/iv/?format=json&indent=on&sites=05288500,%2005331580&parameterCd=00060&siteStatus=all")
        # get data points from Mississippi stream gauges in Memphis (07032000) & Baton Rouge (07374000)
        rawresponse = requests.get("https://waterservices.usgs.gov/nwis/iv/?format=json&indent=on&sites=07032000,%2007374000&parameterCd=00060&siteStatus=all")
        # convert HTML to json
        response = rawresponse.json()
        requestTime = response['value']['queryInfo']['note'][3]
        # get site 1 current data
        siteName0 = response['value']['timeSeries'][0]['sourceInfo']['siteName']
        time0 = response['value']['timeSeries'][0]['values'][0]['value'][0]['dateTime']
        flowRate0 = response['value']['timeSeries'][0]['values'][0]['value'][0]['value']
        # get site 2 current data
        siteName1 = response['value']['timeSeries'][1]['sourceInfo']['siteName']
        time1 = response['value']['timeSeries'][1]['values'][0]['value'][0]['dateTime']
        flowRate1 = response['value']['timeSeries'][1]['values'][0]['value'][0]['value']


        # advance to next time step
        next_step = datetime.now() + timedelta(seconds=5)

        message = {
            "properties":{
                "Request_time":requestTime,
                "Location":{
                    "Memphis, TN":{
                        "Time":time0,
                        "Flow_Rate":flowRate0
                        },
                    "Baton Rouge, LA":{
                        "Time":time1,
                        "Flow_Rate":flowRate1
                        },
                    }
                }
            }

        # publish time and flow rate
        client.publish("userPrefix/streamGauge/flowRate", payload=json.dumps(message))
        print(message)

        # allows application to be stopped with GUI every second
        while datetime.now() < next_step:
           time.sleep(1)
