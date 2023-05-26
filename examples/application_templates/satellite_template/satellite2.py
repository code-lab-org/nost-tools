# -*- coding: utf-8 -*-
"""
    *This application demonstrates a constellation of satellites with continuous data collection and is used to track the state of each satellite's solid-state recorder while its orbital position is propagated from Two-Line Elements (TLEs)*

    The application contains one :obj:`Constellation` (:obj:`Entity`) object class and one :obj:`PositionPublisher` (:obj:`WallclockTimeIntervalPublisher`). The application also contains two global methods outside of these classes, which contain standardized calculations sourced from Ch. 5 of *Space Mission Analysis and Design* by Wertz and Larson.
    
    *NOTE:* For example code demonstrating how the constellation application is started up and how the :obj:`Constellation` :obj:`Entity` object class is initialized and added to the simulator, see the FireSat+ example.

"""

import logging
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
# import numpy as np
import pandas as pd
# import copy
# import matplotlib.pyplot as plt
# import matplotlib.patches as mpatches
# import seaborn as sns

# from scipy import stats

# import time

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.entity import Entity
# from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication
from nost_tools.publisher import WallclockTimeIntervalPublisher

from skyfield.api import load, wgs84, EarthSatellite

from schemas import *
from config import PARAMETERS


logging.basicConfig(level=logging.INFO)


# define an entity to manage satellite updates
class Satellite(Entity):
    """
    *This object class inherits properties from the Entity object class in the NOS-T tools library*

    Args:
        cName (str): A string containing the name for the constellation application
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        id (:obj:`list`): List of unique *int* ids for each satellite in the constellation
        names (:obj:`list`): List of unique *str* for each satellite in the constellation (must be same length as **id**)
        ES (:obj:`list`): Optional list of :obj:`EarthSatellite` objects to be included in the constellation (NOTE: at least one of **ES** or **tles** MUST be specified, or an exception will be thrown)
        tles (:obj:`list`): Optional list of Two-Line Element *str* to be converted into :obj:`EarthSatellite` objects and included in the simulation

    Attributes:
        groundTimes (:obj:`dict`): Dictionary with keys corresponding to unique satellite name and values corresponding to sequential list of ground access opportunities - *NOTE:* each value is initialized as an empty **:obj:`list`** and opportunities are appended chronologically
        grounds (:obj:`DataFrame`): Dataframe containing information about ground stations with unique groundId (*int*), latitude-longitude location (:obj:`GeographicPosition`), min_elevation (*float*) angle constraints, and operational status (*bool*) - *NOTE:* initialized as **None**
        satellites (:obj:`list`): List of :obj:`EarthSatellite` objects included in the constellation - *NOTE:* must be same length as **id**
        positions (:obj:`list`): List of current latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each satellite in the constellation - *NOTE:* must be same length as **id**
        next_positions (:obj:`list`): List of next latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each satellite in the constellation - *NOTE:* must be same length as **id**
        ssr_capacity (:obj:`list`): List of **fixed** Solid-State Recorder (SSR) capacities in Gigabits (*int*) for each satellite in the constellation - *NOTE:* must be same length as **id**
        capacity_used (:obj:`list`): list of values (*float*) representing current fraction of SSR capacity used for each satellite in the constellation, continuously updated through simulation - *NOTE:* must be same length as **id**
        instrument_rates (:obj:`list`): list of **fixed** instrument data collection rates in Gigabits/second (*float*) for each satellite in the constellation - *NOTE:* must be same length as **id**
        cost_mode (:obj:`list`): list of *str* representing one of three cost modes used to update cumulative costs: :obj:`discrete` (per downlink), :obj:`continuous` (fixed contract), or :obj:`both` - *NOTE:* must be same length as **id**
        fixed_rates (:obj:`list`): list of **fixed** rates of cost accumulation in dollars/second for :obj:`continuous` cost_mode for each satellite in the constellation - *NOTE:* must be same length as **id**, but ignored if cost_mode for corresponding satellite is :obj:`discrete`
        linkCounts (:obj:`list`): list of cumulative counts of link opportunies (*int*) for each satellite in the constellation - *NOTE:* must be same length as **id**, initialized as list of zeros
        linkStatus (:obj:`list`): list of states (*bool*) indicating whether or not each satellite in the constellation is currently in view of an available ground station - *NOTE:* must be same length as **id**, each satellite state initialized as :obj:`False`
        cumulativeCostBySat (:obj:`dict`): Dictionary with keys corresponding to unique satellite name and values corresponding to current cumulative costs in dollars (*float*) accrued by each satellite in the constellation, continuously updated throughout the simulation - *NOTE:* must be same length as **id**, each satellite cost initialized as zero dollars
        cumulativeCosts (float): Sum of values in cumulativeCostBySat in dollars, continuously updated throughout the simulation

    """

    ts = load.timescale()

    def __init__(self, cName, app, id, names, ES=None, tles=None):
        super().__init__(cName)
        self.app = app
        self.id = id
        self.names = names
        self.grounds = None
        self.satellite = []
        if ES is not None:
            #for sat in ES:
           self.satellite=ES
        if tles is not None:
            for i, tle in enumerate(tles):
                self.satellites.append(
                    EarthSatellite(tle[0], tle[1], self.names[i], self.ts)
                )
        self.geocentric = self.next_geocentric = None
        self.geocentricPos = self.next_geocentricPos = None
        self.vel = self.next_vel = None
        self.geographicPos = self.next_geographicPos = None

    def initialize(self, init_time):
        """
        Activates the :obj:`Constellation` at a specified initial scenario time

        Args:
            init_time (:obj:`datetime`): Initial scenario time for simulating propagation of satellites
        """
        super().initialize(init_time)
        self.grounds = pd.DataFrame(
            {
                "groundId": pd.Series([], dtype="int"),
                "latitude": pd.Series([], dtype="float"),
                "longitude": pd.Series([], dtype="float"),
                "elevAngle": pd.Series([], dtype="float"),
            }
        )
        self.geocentric = self.satellite.at(self.ts.from_datetime(init_time))
        self.geocentricPos = self.geocentric.position.m
        self.vel = self.geocentric.velocity.m_per_s
        self.geographicPos = self.next_geographicPos = [
            wgs84.subpoint(self.satellite.at(self.ts.from_datetime(init_time)))
        ]
        
        

    def tick(self, time_step):
        """
        Computes the next :obj:`Constellation` state after the specified scenario duration and the next simulation scenario time

        Args:
            time_step (:obj:`timedelta`): Duration between current and next simulation scenario time
        """
        # tik = time.time()
        super().tick(time_step)
        self.next_geocentric = self.satellite.at(
            self.ts.from_datetime(self.get_time() + time_step))
        self.next_geocentricPos = self.next_geocentric.position.m
        self.next_vel = self.next_geocentric.velocity.m_per_s
        self.next_geographicPos = [
            wgs84.subpoint(
                self.satellite.at(self.ts.from_datetime(self.get_time() + time_step))
            )
        ]
        print("THE LAT IS!!!!!!!", self.satellite.latitude.degrees)
        # for i, satellite in enumerate(self.satellites):
        #     then = self.ts.from_datetime(self.get_time() + time_step)
        #     isInRange, groundId = check_in_range(then, satellite, self.grounds)
        #     self.capacity_used[i] = self.capacity_used[i] + ((self.instrument_rates[i]*time_step.total_seconds())/self.ssr_capacity[i])
        #     if self.cost_mode[i] == "continuous" or self.cost_mode[i] == "both":
        #         self.cumulativeCostBySat[self.names[i]] = self.cumulativeCostBySat[self.names[i]] + self.fixed_rates[i]*time_step.total_seconds()
        #         self.cumulativeCosts = self.cumulativeCosts + self.fixed_rates[i]*time_step.total_seconds()
        #     if isInRange:
        #         if not self.linkStatus[i]:
        #             self.linkStatus[i] = True
        #             self.linkCounts[i] = self.linkCounts[i] + 1
        #     else:
        #         if self.linkStatus[i]:
        #             self.linkStatus[i] = False

    def tock(self):
        """
        Commits the next :obj:`Constellation` state and advances simulation scenario time

        """
        # tik = time.time()
        self.geocentric = self.next_geocentric
        self.geocentricPos = self.next_geocentricPos
        self.vel = self.next_vel
        self.geographicPos = self.next_geographicPos
        super().tock()


    def on_ground(self, client, userdata, message):
        """
        Callback function appends a dictionary of information for a new ground station to grounds :obj:`list` when message detected on the *PREFIX/ground/location* topic. Ground station information is published at beginning of simulation, and the :obj:`list` is converted to a :obj:`DataFrame` when the Constellation is initialized.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

        """
        location = GroundLocation.parse_raw(message.payload)
        if location.groundId in self.grounds.groundId:
            self.grounds[
                self.grounds.groundId == location.groundId
            ].latitude = location.latitude
            self.grounds[
                self.grounds.groundId == location.groundId
            ].longitude = location.longitude
            self.grounds[
                self.grounds.groundId == location.groundId
            ].elevAngle = location.elevAngle
            self.grounds[
                self.grounds.groundId == location.groundId
            ].operational = location.operational
            self.grounds[
                self.grounds.groundId == location.groundId
            ].downlinkRate = location.downlinkRate
            self.grounds[
                self.grounds.groundId == location.groundId
            ].costPerSecond = location.costPerSecond
            print(f"Station {location.groundId} updated at time {self.get_time()}.")
        else:
            self.grounds = self.grounds.append(
                {
                    "groundId": location.groundId,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "elevAngle": location.elevAngle,
                    "operational": location.operational,
                    "downlinkRate": location.downlinkRate,
                    "costPerSecond": location.costPerSecond,
                    "costMode": location.costMode
                },
                ignore_index=True,
            )
            print(f"Station {location.groundId} registered at time {self.get_time()}.")
               
            
            
class StatusPublisher(WallclockTimeIntervalPublisher): 

    def __init__(
        self, app, satellite, time_status_step=None, time_status_init=None
    ):
        super().__init__(app, time_status_step, time_status_init)
        self.satellite = satellite
        self.isInRange = False

    def publish_message(self):
        # next_time = self.ES.at(self.ts.from_datetime(
        #     self.get_time() + SCALE * self.time_status_step)
        # )
        # satSpaceTime = self.ES.at(next_time)
        # subpoint = wgs84.subpoint(satSpaceTime)

# self.satellite.ES?
        self.app.send_message(
            "state",
            SatelliteStatus(
                # id=self.satellite.id,
                name=self.satellite.name,
                geocentric_position=list(self.satellite.geocentricPos),
                geographic_position=(self.satellite.geographicPos),
                velocity=list(self.satellite.vel),
                time=self.satellite.get_time(),
            ).json(),
        )

# define a publisher to report satellite status
# class StatusPublisher(WallclockTimeIntervalPublisher):
#     """
#     *This object class inherits properties from the WallclockTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

#     The user can optionally specify the wallclock :obj:`timedelta` between message publications and the scenario :obj:`datetime` when the first of these messages should be published.

#     Args:
#         app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
#         constellation (:obj:`Constellation`): Constellation :obj:`Entity` object class
#         time_status_step (:obj:`timedelta`): Optional duration between time status 'heartbeat' messages
#         time_status_init (:obj:`datetime`): Optional scenario :obj:`datetime` for publishing the first time status 'heartbeat' message

#     """

#     def __init__(
#         self, app, constellation, time_status_step=None, time_status_init=None
#     ):
#         super().__init__(app, time_status_step, time_status_init)
#         self.constellation = constellation


#     def publish_message(self):
#         """
#         *Abstract publish_message method inherited from the WallclockTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

#         This method sends a message to the *PREFIX/constellation/location* topic for each satellite in the constellation (:obj:`Constellation`), which includes:

#         Args:
#             id (int): Unique id for satellite in constellation
#             name (str): Unique *str* name for satellite in constellation
#             latitude (:obj:`confloat`): Latitude in degrees for satellite in constellation at current scenario time
#             longitude (:obj:`confloat`): Longitude in degrees for satellite in constellation at current scenario time
#             altitude (float): Altitude above sea-level in meters for satellite in constellation at current scenario time
#             capacity_used (float): Fraction of solid-state recorder capacity used for satellite in constellation at current scenario time
#             commRange (bool): Boolean state variable indicating if satellite in constellaton is in view of a ground station at current scenario time
#             groundId (int): Optional unique id for ground station in view of satellite in constellation at current scenario time (if commRange = False, the groundId = None)
#             totalLinkCount (int): Unique count of downlink opportunities for satellite in constellation
#             cumulativeCostBySat (float): Cumulative costs incurred for downlinks and/or fixed cost contracts for satellite in constellation at current scenario time
#             time (:obj:`datetime`): Current scenario :obj:`datetime`

#         """
#         for i, satellite in enumerate(self.constellation.satellites):
#             next_time = constellation.ts.from_datetime(
#                 constellation.get_time() + 60 * self.time_status_step
#             )
#             satSpaceTime = satellite.at(next_time)
#             subpoint = wgs84.subpoint(satSpaceTime)
#             self.isInRange[i], groundId = check_in_range(
#                 next_time, satellite, constellation.grounds
#             )
#             self.app.send_message(
#                 "location",
#                 SatelliteStatus(
#                     id=i,
#                     name=self.constellation.names[i],
#                     latitude=subpoint.latitude.degrees,
#                     longitude=subpoint.longitude.degrees,
#                     altitude=subpoint.elevation.m,
#                     capacity_used=self.constellation.capacity_used[i]*self.constellation.ssr_capacity[i],
#                     commRange=self.isInRange[i],
#                     groundId=groundId,
#                     totalLinkCount=self.constellation.linkCounts[i],
#                     cumulativeCostBySat=self.constellation.cumulativeCostBySat[self.constellation.names[i]],
#                     time=constellation.get_time(),
#                 ).json(),
#             )


