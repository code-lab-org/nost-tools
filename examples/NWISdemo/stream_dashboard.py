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


def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    # setting up list of dictionaries
    gageHeightMessage = json.loads(msg.payload.decode("utf-8"))
    gageLOD.append(gageHeightMessage)
    update_fig(n)

    
def update_fig(n):
<<<<<<< Updated upstream
    df = pd.DataFrame(gageLOD)
    print(df)
    df.to_csv(index=False)

    # fig = px.line(df, x='requestTime', y='gageHeight', color='siteName', markers=True,
=======
    df["siteName"] = pd.Series(gageHeightMessage["siteName"])
    df["requestTime"] = datetime.strptime(gageHeightMessage["requestTime"]['value'],"%Y-%m-%dT%H:%M:%S.%fZ")
    df["gageHeight"] = gageHeightMessage["gageHeight"]
    
    
    # fig = px.line(df, x='requestTime', y='gageHeight', color='Index', markers=True,
>>>>>>> Stashed changes
    #                   labels={"requestTime":"Request Time", "gageHeight":"Gage Height (ft)"},
    #                   title='NWIS Gage Heights')
    # return fig

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
<<<<<<< Updated upstream
=======

    # initialize df
    columns = {
        "requestTime": pd.Series([], dtype="datetime64[ns, utc]"),
        "siteName": pd.Series([], dtype="object"),
        "dataTime": pd.Series([], dtype="datetime64[ns, utc]"),
        "gageHeight": pd.Series([], dtype="float"),
        "latitude": pd.Series([], dtype="float"),
        "longitude": pd.Series([], dtype="float"),
    }
    
    df = pd.DataFrame(columns, index=[0])
>>>>>>> Stashed changes
    
    # initialize df   
    df0 = pd.DataFrame()
    df0["requestTime"] = 0
    df0['siteName'] = "nan"
    df0['dataTime'] = 0
    df0['gageHeight'] = 0
    df0['latitude'] = 0
    df0['longitude'] = 0
    n=0
<<<<<<< Updated upstream
    gageLOD = []
=======
    #gageHeightMessage = []
    gageHeightMessage=[]
>>>>>>> Stashed changes

    app = dash.Dash(__name__)

    # for dashboard plot
<<<<<<< Updated upstream
    fig = px.line(df0, x='requestTime', y='gageHeight', color='siteName', markers=True,
                      labels={"requestTime":"Request Time", "gageHeight":"Gage Height (ft)"},
                      title='NWIS Gage Heights')
=======
    # fig = px.line(df, x='requestTime', y='gageHeight', color='siteName', markers=True,
    #                   labels={"requestTime":"Request Time", "gageHeight":"Gauge Height (ft)"},
    #                   title='NWIS Gage Heights')
>>>>>>> Stashed changes

    # app.layout = html.Div([
    #     dcc.Graph(
    #         id='Flow_Rate_Plot', figure=fig
    #         ),
    #     dcc.Interval(
    #         id="interval-component",
    #         interval=1*1000,
    #         n_intervals=0
    #     )
    # ])

    app.callback(Output('Flow_Rate_Plot', 'figure'),Input("interval-component", 'n_intervals'))(update_fig)
<<<<<<< Updated upstream
    
    app.run_server(debug=True)


=======

    # app.run_server(debug=True)
>>>>>>> Stashed changes
