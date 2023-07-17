# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 16:07:23 2023

@author: mlevine4
"""

import json
from dash import dash, dcc, html # type:ignore
import dash_daq as daq # type:ignore
from dash.dependencies import Input, Output # type:ignore
import plotly.express as px # type:ignore
import pandas as pd # type:ignore
# from datetime import datetime, timedelta
from dotenv import dotenv_values # type:ignore

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver # type:ignore
from nost_tools.managed_application import ManagedApplication # type:ignore

from utilityDashboard_config_files.config import PREFIX, NAME # type:ignore
from utilityDashboard_config_files.schema import UtilityPub # type:ignore

def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    # setting up list of dictionaries
    messageIn = json.loads(msg.payload.decode("utf-8"))
    print(messageIn)
    if (msg.topic == f"{PREFIX}/eventGenerator/utilityPredict") | (msg.topic == f"{PREFIX}/eventGenerator/utilityReal"):
        utilityLOD.append(messageIn)
        update_utility(n_utility)
    elif msg.topic == f"{PREFIX}/manager/start":
        print("\n\nDid the manager start trigger work?!!\n\n")
        print(msg.topic)        
    elif msg.topic == f"{PREFIX}/manager/stop":
        print("\n\nDid the manager stop trigger work?!!\n\n")
        print(msg.topic)
        print("\nAll done?\n")
        
    
def update_utility(n_utility):
    df0 = pd.DataFrame(utilityLOD)
    utilityFig = px.line(df0, x="time", y="utility", color="eventId", linestyle="type", markers=True,
                          labels={"time":"time (UTC)", "utility":"Expected science utility returned, u(t)", "eventId":"eventId"},
                          title="Utility v. Time")
    return utilityFig

# def update_predict(n_predict):
#     df0 = pd.DataFrame(utilityPredictLOD)
#     predictFig = px.line(df0, x="timePredict", y="utilityPredict", color="eventId", markers=True,
#                           labels={"time":"time (UTC)", "utilityPredict":"Expected science utility returned, u(t)", "eventId":"eventId"},
#                           title="Predicted Utility v. Time")
#     return predictFig

# def update_real(n_real):
#     df0 = pd.DataFrame(utilityRealLOD)
#     realFig = px.area(df0, x="timReal", y="utilityReal", color="eventId", markers=False,
#                       labels={"time":"time (UTC)", "utilityReal":"Actual science utility returned, u(t)", "eventId":"eventId"},
#                       title="Real Utility v. Time")
#     return realFig

def disable_dash(state_switch):
    if state_switch:
        state = False
    else:
        state = True
    return state


# name guard
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"]) # type:ignore
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]
    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)
    # create the managed application
    app = ManagedApplication(NAME)
    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))   
    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PREFIX,
        config
    )
    # Add on_message callbacks, sort through with if statements for now
    # app.add_message_callback("eventGenerator", "eventStart", on_message)
    app.add_message_callback("eventGenerator", "utilityPredict", on_message)
    app.add_message_callback("eventGenerator", "utilityReal", on_message)
    app.add_message_callback("manager", "start", on_message)
    app.add_message_callback("manager", "stop", on_message)

    # initialize df0
    df0 = pd.DataFrame()
    df0["eventId"] = 0
    df0["latitude"] = 0
    df0["logitude"] = 0
    df0["time"] = 0
    df0["isDay"] = 0
    df0["utility"] = 0
    df0["isReal"] = 0

    state_switch = False

    n_utility = 0
    utilityLOD = [] # type:ignore
    state = True
    
    utilityDashboard = dash.Dash(__name__)

    # for dashboard plot
    utilityFig = px.line(df0, x="time", y='utility', color='eventId', linestyle='type', markers=True, mode="lines+markers",
                          labels={"time":"time (UTC)", "utility":"Normalized Science Return", "eventId":"eventId", "type":"Predicted or Real Utility?"},
                          title="Science Utility v Time")
    
    
    
    utilityDashboard.layout = html.Div([
        dcc.Graph(
            id="Utility_Plot", 
            figure=utilityFig,
            config={
                'toImageButtonOptions': {
                    'format': 'svg'
                }
            }
        ),
        dcc.Interval(
            id="interval-utility",
            interval=1*1000,
            n_intervals=n_utility,
            disabled=state
        ),
        daq.BooleanSwitch(id="disable-switch", on=state_switch)
    ])

    utilityDashboard.callback(Output("Utility_Plot", 'figure'),Input("interval-capacity", 'n_intervals'),prevent_initial_call=True)(update_capacity)
    utilityDashboard.callback([Output("interval-capacity", 'disabled'),Output("interval-cost",'disabled')],Input("disable-switch","on"),prevent_initial_call=True)(disable_dash)

    utilityDashboard.run_server(debug=True)