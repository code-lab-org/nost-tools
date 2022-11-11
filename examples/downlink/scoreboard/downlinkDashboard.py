# -*- coding: utf-8 -*-
"""
    This application creates a dashboard that displays the amount of data in 
    each S/C hard drive.
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
from dotenv import dotenv_values



def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    # setting up list of dictionaries
    messageIn = json.loads(msg.payload.decode("utf-8"))
    if msg.topic == "downlink/constellation/location":
        eventLOD.append(messageIn)   
        update_fig(n)
    elif msg.topic == "downlink/constellation/linkCharge": #"downlink/ground/linkCharge":
        eventLOD1.append(messageIn)
        update_fig1(n1)
    print(messageIn)
    
def update_fig(n):
    df0 = pd.DataFrame(eventLOD)
    fig = px.line(df0, x="time", y='capacity_used', color='name', markers=True,
                          labels={"time":"time", "capacity_used":"Amount of Data in HD (GB)"},
                          title="Hard Drive Space Used")
    return fig

def update_fig1(n1):
    df1 = pd.DataFrame(eventLOD1)
    fig1 = px.line(df1, x="end", y='cumulativeCostbySat', color='satName', markers=True,
                          labels={"end":"time", "cumulativeCostbySat":"Cumulative Costs ($)"},
                          title="Cost Expenditure")
    return fig1




# name guard
if __name__ == "__main__":
    
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]
    # build the MQTT client
    client = mqtt.Client()
    # set client username and password
    client.username_pw_set(username=USERNAME, password=PASSWORD)
    # set tls certificate
    client.tls_set()
    # connect to MQTT server on port 8883
    client.connect(HOST, PORT)
    # subscribe to science event topics
    subList = [("downlink/constellation/location",0), ("downlink/ground/linkCharge",0),("downlink/constellation/linkCharge",0)]
    client.subscribe(subList)
    # bind the message handler
    client.on_message = on_message
    client.loop_start()


    # initialize df0
    df0 = pd.DataFrame()
    df0["id"] = 0
    df0["name"] = 0
    df0["latitude"] = 0
    df0["longitude"] = 0
    df0["altitude"] = 0
    df0["capacity_used"] = 0
    df0["commRange"] = 0
    df0["groundID"] = 0
    df0["time"] = 0


    n=0
    eventLOD = []
    
    df1 = pd.DataFrame()
    df1["groundId"] = 0
    df1["satId"] = 0
    df1["satName"] = 0
    df1["linkId"] = 0
    df1["end"] = 0
    df1["duration"] = 0
    df1["dataOffload"] = 0
    df1["downlinkCost"] = 0
    df1["cumulativeCostbySat"] = 0
    df1["cumulativeCosts"] = 0

    n1=0
    eventLOD1 = []
    
    app = dash.Dash(__name__)

    # for dashboard plot
    fig = px.line(df0, x="time", y='capacity_used', color='name', markers=True,
                          labels={"time":"time", "capacity_used":"Amount of Data in HD (GB)"},
                          title="Hard Drive Space Used")
    
    fig1 = px.line(df1, x="end", y='cumulativeCostbySat', color='satName', markers=True,
                          labels={"end":"time", "cumulativeCostbySat":"Cumulative Costs ($)"},
                          title="Cost Expenditure")
    
    

    app.layout = html.Div([
        dcc.Graph(
            id="Utility_Plot", figure=fig
            ),
        dcc.Interval(
            id="interval-component",
            interval=1*1000,
            n_intervals=0
        ),
        dcc.Graph(
            id="Cost_Plot", figure=fig1
            ),
        dcc.Interval(
            id="interval-component2",
            interval=1*1000,
            n_intervals=0
        )
    ])

    app.callback(Output("Utility_Plot", 'figure'),Input("interval-component", 'n_intervals'))(update_fig)
    app.callback(Output("Cost_Plot", 'figure'),Input("interval-component2", 'n_intervals'))(update_fig1)

    app.run_server(debug=True)
    