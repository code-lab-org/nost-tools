# -*- coding: utf-8 -*-
"""
    *An application that prints science utility values to a dashboard.*


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



def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    # setting up DataFrame
    eventMessage = json.loads(msg.payload.decode("utf-8"))
    list_of_dicts.append(eventMessage)
    print("LIST", eventMessage)
    update_fig(n)

    
def update_fig(n):
    df = pd.DataFrame(list_of_dicts)
    print("DATAFRAME", df)
    fig = px.line(df, x='time', y='utility', color='latitude', markers=True,
                          labels={"time":"time", "utility":"utility (n.d.)"},
                          title="Science Event Utility")
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
    client.subscribe("BCtest/AIAA/eventUtility",0)
    # bind the message handler
    client.on_message = on_message
    # start a background thread to let MQTT do things
    client.loop_start()
    
    # initialize df
    df0 = pd.DataFrame()
    df0["time"] = 0
    df0["latitude"] = 0
    df0["longitude"] = 0
    df0["utility"] = 0
    n=0
    list_of_dicts = []

    app = dash.Dash(__name__)

    # for dashboard plot
    fig = px.line(df0, x='time', y='utility', color='latitude', markers=True,
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
