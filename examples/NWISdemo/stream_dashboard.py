# -*- coding: utf-8 -*-
"""
This application displays a dashboard of all gage heights.
"""

import paho.mqtt.client as mqtt
import json
import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
import csv
from dash.dependencies import Input, Output, State


def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    # setting up list of dictionaries
    # gageHeightMessage = json.loads(msg.payload.decode("utf-8"))
    # df = pd.DataFrame({'siteName':gageHeightMessage["siteName"]})
    # df["requestTime"] = (datetime.strptime(gageHeightMessage["requestTime"]['value'],"%Y-%m-%dT%H:%M:%S.%fZ"))
    # df["gageHeight"] = (gageHeightMessage["gageHeight"])
    # gageLOD.append(gageHeightMessage)

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
    #df2 = pd.DataFrame(gageLOD)
    # print(df)
    #df.to_csv(index=False)

    # df["siteName"] = pd.DataFrame(gageLOD[0]["siteName"]["value"])
    # df["requestTime"] = pd.DataFrame(datetime.strptime(gageLOD[0]["requestTime"]['value'],"%Y-%m-%dT%H:%M:%S.%fZ"))
    # df["gageHeight"] = pd.DataFrame(gageLOD[0]["gageHeight"])


    # df4 = pd.DataFrame({'siteName':gageLOD[0]["siteName"]})
    # df4["requestTime"] = (datetime.strptime(gageLOD[0]["requestTime"]['value'],"%Y-%m-%dT%H:%M:%S.%fZ"))
    # df4["gageHeight"] = (gageLOD[0]["gageHeight"])

    # with open('gageLOD', 'w') as fout:
    #     json.dump(gageLOD, fout)

    # df.append(df)

    plotData = pd.read_csv(filename)
    dffig = pd.DataFrame(data=plotData)

    fig = px.line(dffig, x='requestTime', y='gageHeight', color='siteName', markers=True,
                      labels={"requestTime":"Request Time", "gageHeight":"Gage Height (ft)"},
                      title='NWIS Gage Heights')
    return fig

# name guard
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
    # subscribe to flow rate topic
    client.subscribe("BCtest/streamGauge/gageHeight",0)
    # bind the message handler
    client.on_message = on_message
    # start a background thread to let MQTT do things
    client.loop_start()

    # initialize df
    columns = {
        "requestTime": pd.Series([], dtype="datetime64[ns, utc]"),
        "siteName": pd.Series([], dtype="str"),
        "dataTime": pd.Series([], dtype="datetime64[ns, utc]"),
        "gageHeight": pd.Series([], dtype="float"),
        "latitude": pd.Series([], dtype="float"),
        "longitude": pd.Series([], dtype="float"),
    }

    df = pd.DataFrame(columns)


    n=0
    gageHeightMessage = []

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
