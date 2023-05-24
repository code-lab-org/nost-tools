# -*- coding: utf-8 -*-
"""
Created on Thu Apr 27 17:54:11 2023

@author: mlevine4
"""

#Import necessary modules and functions
import logging
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
from tatc.schemas import Satellite, TwoLineElements, GroundStation # type: ignore
from tatc.analysis import collect_downlinks # type: ignore
from skyfield.api import load # type: ignore
import pandas as pd # type: ignore
from pydantic import BaseModel, Field
# from typing import Optional
# import matplotlib.pyplot as plt # type: ignore

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver # type: ignore
from nost_tools.entity import Entity # type: ignore
from nost_tools.managed_application import ManagedApplication # type: ignore


logging.basicConfig(level=logging.INFO)    

# Define a function to read a tle file and return a dictionary of TATC Satellite objects
def read_file_to_satellite_dict(path):
    #Open the file and read its contents
    with open(path) as f:
        lines = f.readlines()

    #group the lines into chunks of three
    satdef = []

    while len(lines) > 0:
        chunk = []
        for x in range(3):
            chunk.append(lines.pop(0).replace('\n', '').strip())
        satdef.append(chunk)
    #create a dictionary of Satellite objects
    satellites = {}
    for satellite in satdef:
        sat = Satellite(
            name= satellite[0],
            orbit=TwoLineElements(
                tle=[
                    satellite[1],
                    satellite[2],
                ]
            ),
            instruments=[],
        )
        satellites[satellite[0]] = sat
    return satellites

class CurrentView(BaseModel):
    """
    
    """
    timestamp: datetime = Field(..., description="Timestamp associated with the change in state")
    ground: str = Field(..., description="Unique name for ground identifier")
    numInView: int = Field(..., description="Number of satellites in view")


class SatsInView(Entity):
    """
    *This object class inherits properties from the Entity object class in the NOS-T tools library*
    """
    ts = load.timescale()
    
    def __init__(self, app, grounds, df, start, interval):
        self.app = app
        self.grounds = grounds
        self.df_SatInView = df
        self.current_refTime = start
        self.next_refTime = start + interval
        self.interval = interval
        self.advance = False
        
    def initialize(self, init_time):
        """
        Activates the :obj:`SatsInView` at a specified initial scenario time

        Args:
            init_time (:obj:`datetime`): Initial scenario time for simulating propagation of satellites
        """
        super().initialize(init_time)
        for index, ground in self.grounds.iterrows():
            self.app.send_message(
                "currentSats",
                CurrentView(
                    timestamp=self.current_refTime,
                    ground=ground.name,
                    numInView=self.df_SatInView[ground.name][self.current_refTime],
                    ).json(),
                )
        
    def tick(self, time_step):
        """
        Computes the next :obj:`SatsInView` state after the specified scenario duration and the next simulation scenario time

        Args:
            time_step (:obj:`timedelta`): Duration between current and next simulation scenario time
        """
        super().tick(time_step)
        then = self.ts.from_datetime(self.get_time() + time_step)
        if then >= self.next_refTime:
            self.advance = True
        
    def tock(self):
        """
        Commits the next :obj:`SatsInView` state and advances simulation scenario time

        """
        if self.advance:
            self.current_refTime = self.next_refTime
            self.next_refTime = self.next_refTime + self.interval
            for index, ground in self.grounds.iterrows():
                self.app.send_message(
                    "currentSats",
                    CurrentView(
                        timestamp=self.current_refTime,
                        ground=ground.name,
                        numInView=int(self.df_SatInView[ground.name][self.current_refTime]),
                        )
                    )
        super().tock()

# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # load current TLEs for active satellites from Celestrak (NOTE: User has option to specify their own TLE instead)
    activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
    load.tle_file(activesats_url, reload=True)
    activesats = read_file_to_satellite_dict("./active.txt")
    # activesats = load.tle_file(activesats_url, reload=True)
    # by_name = {sat.name: sat for sat in activesats}
    
    # Define a list of names for the satellites to be analyzed
    names = ["AQUA","FENGYUN","DMSP", "NOAA", "SUOMI", "METEOR-M","METOP-B","METOP-C","METEOR-M2","SARSAT","HJ-1A","HJ-1B","DMC3-FM1","DMC3-FM2","DMC3-FM3","LANDSAT","TERRA","AURA","AIM","WISE","FLOCK"]
    
    ES = []
    for sat in activesats.keys():
        if sat[:sat.find(" ")] in names:
            ES.append(activesats[sat])
            
    # define grounds in a Dataframe constructed from a Python dictionary
    MIN_ELEVATION_AWS = 20.0  # minimum view angle (degrees) for ground-satellite communications
        
    GROUND = pd.DataFrame(
        # Currently available AWS stations
        data={
            "groundId": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "name": ["Ohio", "Oregon", "Hawaii", "Sydney", "Seoul", "Bahrain", "Cape Town", "Stockholm", "Ireland", "Punta Arenas", "Singapore"],
            "latitude": [40.1625, 43.8041, 19.8968, -33.8688, 37.5665, 26.0667, -33.9249, 59.3293, 53.1424, -53.1638, 1.2840],
            "longitude": [-83.21, -120.5542, -155.5828, 151.2093, 126.978, 50.5577, 18.4241, 18.0686, -7.6921, -70.9171, 103.8488],
            "min_elevation_angle": [MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS, MIN_ELEVATION_AWS],
            "operational": [True, True, True, True, True, True, True, True, True, True, True],
            "maxSatsServed": [2, 4, 3, 6, 7, 9, 20, 22, 10, 3, 11]
        }
    )
    
    AWS_GS = []
    
    for index, row in GROUND.iterrows():
        GS = GroundStation(name=row["name"], latitude=row["latitude"], longitude=row["longitude"], min_elevation_angle=row["min_elevation_angle"])
        AWS_GS.append(GS)
        
    start = datetime(year=2023, month=5, day=1, hour=12, tzinfo=timezone.utc)
    end = start + timedelta(days=2)
    
    data_SatsInView = {} # type: dict
    downlink_data = {} # type: dict
    all_data = {} # type: dict
    numSatsPerTime = {} # type: dict
    
    # Collect downlink data for each ground station for each selected satellite
    for ground in AWS_GS:
        for sat in ES:
            downlink_data[sat.name] = collect_downlinks(ground, sat, start, end)
    
        # Combine and sort the downlink data for all satellites
        data_SatsInView[ground.name] = pd.concat(downlink_data.values()).sort_values(by=["start"])
        numSatsPerTime[ground.name] = {}
        downlink_data = {}
    # all_data = pd.concat(data_SatsInView.values()).sort_values(by=["start"])
    
    # Plot the number of satellites in view of the ground station during each interval
    interval = timedelta(minutes=5)
    start_copy = start
    while start_copy < end:
        for ground in AWS_GS:
            #determines the number of satellites in view at the current time interval
            numSatsPerTime[ground.name][start_copy] = len(data_SatsInView[ground.name].loc[((data_SatsInView[ground.name]["start"] < start_copy) & (data_SatsInView[ground.name]["end"] > start_copy)) | ((data_SatsInView[ground.name]["start"] > start_copy) & (data_SatsInView[ground.name]["start"] < (start_copy + interval)))])
        #Use a '#' to comment either of the sat_dict, the first allows the data to be plotted while the second allows it to be save into a seperate file
        #determines the number of satellites in view and states their names, Start, and end at the current time interval
        #sat_dict[start_copy] = combined_downlinks.loc[((combined_downlinks["start"] < start_copy) & (combined_downlinks["end"] > start_copy)) | ((combined_downlinks["start"] > start_copy) & (combined_downlinks["start"] < (start_copy + interval)))]
        start_copy = start_copy + interval
        
    # Convert the dictionary to a DataFrame
    df_SatsInView = pd.DataFrame.from_dict(numSatsPerTime, orient='columns')
        
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)
    
    # create the managed application
    app = ManagedApplication("satsInView")
    
    SatInViewObj = SatsInView(app, GROUND, df_SatsInView, start, interval)
    
    # add the environment observer to monitor for fire status events
    app.simulator.add_entity(SatInViewObj)
    
    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        "InView",
        config,
        True,
        time_status_step=timedelta(seconds=10) * 300,
        time_status_init=start,
        time_step=timedelta(seconds=1) * 300,
    )