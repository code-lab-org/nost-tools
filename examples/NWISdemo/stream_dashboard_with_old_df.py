# -*- coding: utf-8 -*-
"""
This application displays a dashboard of all gage heights.
"""

import paho.mqtt.client as mqtt
import json
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import json
import csv


def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    
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
    update_fig(n)

    
def update_fig(n):
    
    plotData = pd.read_csv(filename)
    dffig = pd.DataFrame(data=plotData)
       
    fig = px.line(dffig, x='requestTime', y='gageHeight', color='siteName', markers=True,
                      labels={"requestTime":"Request Time", "gageHeight":"Gage Height (ft)"},
                      title='NWIS Gage Heights')
    return fig

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
    # subscribe to flow rate topic
    client.subscribe("BCtest/streamGauge/gageHeight",0)
    # bind the message handler
    client.on_message = on_message
    # start a background thread to let MQTT do things
    client.loop_start()

    df=[]   
    n=0
    fields = ['siteName','requestTime','dataTime','gageHeight','latitude','longitude']
    # name of output file
    filename = "gageHeight.csv"
    with open(filename, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)
        # writing the fields
        csvwriter.writerow(fields)
    gageLOD = []

    gageHeightMessage=[]

    app = dash.Dash(__name__)

    # for dashboard plot
    fig = px.line(df, x='requestTime', y='gageHeight', color='siteName', markers=True,
                      labels={"requestTime":"Request Time", "gageHeight":"Gage Height (ft)"},
                      title='NWIS Gage Heights')

    app.layout = html.Div([
        dcc.Graph(
            id='Flow_Rate_Plot', figure=fig
            ),
        dcc.Interval(
            id="interval-component",
            interval=1*1000,
            n_intervals=0
        )
    ])

    app.callback(Output('Flow_Rate_Plot', 'figure'),Input("interval-component", 'n_intervals'))(update_fig)
    
    app.run_server(debug=True)

