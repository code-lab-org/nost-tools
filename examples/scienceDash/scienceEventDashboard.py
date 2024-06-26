# -*- coding: utf-8 -*-
"""
    This application demonstrates how to create a simple dashboard for
    visualizing NOS-T data in real time. It subscribes to the
    scienceEventPublisher.py application and displays the science utility
    separated by location.
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
    """ Callback to process an incoming message and then run the update_fig function."""
    eventMessage = json.loads(msg.payload.decode("utf-8"))
    eventMessage["location"] = eventMessage["latitude"], eventMessage["longitude"]
    eventLOD.append(eventMessage)
    update_fig(n)

def update_fig(n):
    """ Updates the dashboard when new data is received."""
    df = pd.DataFrame(data=eventLOD)
    fig = px.line(df, x='time', y='utility', color='location', markers=True,
                          labels={"time":"time", "utility":"utility (n.d.)"},
                          title="Science Event Utility")
    return fig

# name guard
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
    # subscribe to science event topics
    client.subscribe("BCtest/AIAA/eventUtility",0)
    # bind the message handler
    client.on_message = on_message
    # start a background thread to let MQTT do things
    client.loop_start()

    # initialize df
    df0 = pd.DataFrame()
    latitude = 0
    longitude = 0
    df0["latitude"] = 0
    df0["longitude"] = 0
    df0["time"] = 0
    df0["utility"] = 0
    df0["location"] = (latitude, longitude)
    n=0
    eventLOD = []

    app = dash.Dash(__name__)

    # for dashboard plot
    fig = px.line(df0, x='time', y='utility', color='location', markers=True,
                          labels={"time":"time", "utility":"utility (n.d.)"},
                          title="Science Event Utility")

    app.layout = html.Div([
        dcc.Graph(
            id="Utility_Plot", figure=fig
            ),
        dcc.Interval(
            id="interval-component",
            interval=1*1000,
            n_intervals=0
        )
    ])

    app.callback(Output("Utility_Plot", 'figure'),Input("interval-component", 'n_intervals'))(update_fig)

    app.run_server(debug=True)
