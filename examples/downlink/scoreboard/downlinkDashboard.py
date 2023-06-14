# -*- coding: utf-8 -*-
"""
    *This application demonstrates a plotly dashboard for tracking hard-drive state and cumulative costs for the downlink example case.*

    This application is under development.

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
# from nost_tools.simulator import Simulator, Mode
# from nost_tools.observer import Observer, Observable
from nost_tools.managed_application import ManagedApplication # type:ignore

from downlinkDashboard_config_files.config import PREFIX, NAME # type:ignore

def on_message(mqttc, obj, msg):
    """ Callback to process an incoming message."""
    # setting up list of dictionaries
    messageIn = json.loads(msg.payload.decode("utf-8"))
    print(messageIn)
    if msg.topic == f"{PREFIX}/constellation/location":
        capacityLOD.append(messageIn)   
        update_capacity(n_capacity)
        update_cost(n_cost)
    elif msg.topic == f"{PREFIX}/constellation/linkCharge" or msg.topic == f"{PREFIX}/ground/linkCharge":
        # if not state_cost:
        print(msg.topic)
        print("\n\n linkCharge \n\n")
        print(messageIn)
        costLOD.append(messageIn)
    elif msg.topic == f"{PREFIX}/manager/start":
        print("\n\nDid the manager start trigger work?!!\n\n")
        print(msg.topic)        
    elif msg.topic == f"{PREFIX}/manager/stop":
        print("\n\nDid the manager stop trigger work?!!\n\n")
        print(msg.topic)
        app.shut_down()
        print("\nAll done?\n")
        
def update_capacity(n_capacity):
    df0 = pd.DataFrame(capacityLOD)
    capacityFig = px.line(df0, x="time", y='capacity_used', color='name', markers=True,
                          labels={"time":"time (UTC)", "capacity_used":"Amount of Data in HD (GB)", "name":"Satellite Name"},
                          title="Hard Drive Space Used")
    
    return capacityFig

def update_cost(n_cost):
    df0 = pd.DataFrame(capacityLOD)
    costFig = px.area(df0, x="time", y='cumulativeCostBySat', color='name', markers=False,
                      labels={"time":"time (UTC)", "cumulativeCostBySat":"Cumulative Costs ($)", "name":"Satellite Name"},
                      title="Cost Expenditure")
    return costFig

def disable_dash(state_switch):
    if state_switch:
        state_capacity = False
        state_cost = False
    else:
        state_capacity = True
        state_cost = True
    return state_capacity, state_cost

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
    app.add_message_callback("constellation", "location", on_message)
    app.add_message_callback("constellation", "linkCharge", on_message)
    app.add_message_callback("ground", "linkCharge", on_message)
    app.add_message_callback("manager", "start", on_message)
    app.add_message_callback("manager", "stop", on_message)

    # initialize df0
    df0 = pd.DataFrame()
    df0["id"] = 0
    df0["name"] = 0
    df0["latitude"] = 0
    df0["longitude"] = 0
    df0["altitude"] = 0
    df0["capacity_used"] = 0
    df0["ssr_capacity"] = 0
    df0["commRange"] = 0
    df0["groundID"] = 0
    df0["totalLinkCount"] = 0
    df0["cumulativeCostBySat"] = 0.00
    df0["cumulativeCost"] = 0.00
    df0["time"] = 0

    state_switch = False

    n_capacity=0
    capacityLOD = [] # type:ignore
    state_capacity = True
    
    df1 = pd.DataFrame()
    df1["groundId"] = 0
    df1["satId"] = 0
    df1["satName"] = 0
    df1["linkId"] = 0
    df1["end"] = 0
    df1["duration"] = 0
    df1["dataOffload"] = 0
    df1["downlinkCost"] = 0
    df1["cumulativeCostBySat"] = 0
    df1["cumulativeCosts"] = 0

    n_cost=0
    costLOD = [] # type:ignore
    state_cost = True
    
    downlinkDashboard = dash.Dash(__name__)

    # for dashboard plot
    capacityFig = px.line(df0, x="time", y='capacity_used', color='name', markers=True,
                          labels={"time":"time (UTC)", "capacity_used":"Amount of Data in HD (GB)", "name":"Satellite Name"},
                          title="Hard Drive Space Used")
    
    costFig = px.area(df0, x="time", y='cumulativeCostBySat', color='name', markers=True,
                          labels={"time":"time (UTC)", "cumulativeCostBySat":"Cumulative Costs ($)", "name":"Satellite Name"},
                          title="Cost Expenditure")
    
    downlinkDashboard.layout = html.Div([
        dcc.Graph(
            id="Capacity_Plot", 
            figure=capacityFig,
            config={
                'toImageButtonOptions': {
                    'format': 'svg'
                }
            }
        ),
        dcc.Interval(
            id="interval-capacity",
            interval=1*1000,
            n_intervals=n_capacity,
            disabled=state_capacity
        ),
        dcc.Graph(
            id="Cost_Plot", 
            figure=costFig,
            config={
                'toImageButtonOptions': {
                    'format': 'svg'
                }
            }
        ),
        dcc.Interval(
            id="interval-cost",
            interval=1*1000,
            n_intervals=n_cost,
            disabled=state_capacity
        ),
        daq.BooleanSwitch(id="disable-switch", on=state_switch)
    ])

    downlinkDashboard.callback(Output("Capacity_Plot", 'figure'),Input("interval-capacity", 'n_intervals'),prevent_initial_call=True)(update_capacity)
    downlinkDashboard.callback(Output("Cost_Plot", 'figure'),Input("interval-cost", 'n_intervals'),prevent_initial_call=True)(update_cost)
    downlinkDashboard.callback([Output("interval-capacity", 'disabled'),Output("interval-cost",'disabled')],Input("disable-switch","on"),prevent_initial_call=True)(disable_dash)

    downlinkDashboard.run_server(debug=True)
    