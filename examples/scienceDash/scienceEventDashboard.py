# -*- coding: utf-8 -*-
"""
    *An application that gets stream data and publishes it to NOS-T.*

    This application subscribes to the *BCtest/streamGauge/flowrate* topic and
    uses a callback function to collect the time and flow rate data every time
    stream_gauge.py publishes. This data is then saved to a .csv file for the
    stream_dashboard.py application.
"""

import paho.mqtt.client as mqtt
import csv
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta



def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    # setting up DataFrame 
    eventMessage = json.loads(msg.payload.decode("utf-8"))
    time = eventMessage["time"]
    latitude = eventMessage["latitude"]
    longitude = eventMessage["longitude"]
    utility = eventMessage["utility"]

    df = pd.DataFrame.from_dict(eventMessage)
    
    # def update_fig(n):
    #     dffig = df
    #     fig = px.line(dffig, x='time', y='utility', color='latitude', markers=True,
    #                       labels={"time":"time", "utility":"utility (n.d.)"},
    #                       title="Science Event Utility")
    #     return fig
    
    # fig = px.line(df, x='time', y='utility', color='latitude', markers=True,
    #                       labels={"time":"time", "utility":"utility (n.d.)"},
    #                       title="Science Event Utility")
    
    
    print(df)


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
    
    # intialize df
    currentTime = datetime.now()
    global eventMessage
    eventMessage = {"time":[currentTime.strftime('%H%M%S')],
                    "latitude":[0],
                    "longitude":[0],
                    "utility":[0]}
    df = pd.DataFrame.from_dict(eventMessage)

       
    app = dash.Dash(__name__)
    
    # defining dashboard figure
    fig = px.line(df, x='time', y='utility', color='latitude', markers=True,
                          labels={"time":"time", "utility":"utility (n.d.)"},
                          title="Science Event Utility")
    
    app.layout = html.Div([
        dcc.Graph(
            id='Utility_Plot', figure=fig
            ),
        dcc.Interval(
            id="interval-component",
            interval=1*1000,
            n_intervals=0
        )
    ])
    
    @app.callback(
        Output("Utility_Plot", 'figure'),
        [Input("interval-component", 'n_intervals')]
    )
    
    def update_fig(n):
        fig = px.line(df, x='time', y='utility', color='latitude', markers=True,
                              labels={"time":"time", "utility":"utility (n.d.)"},
                              title="Science Event Utility")
        return fig
    
    
    if __name__ == '__main__':
        app.run_server(debug=True)



    



    
