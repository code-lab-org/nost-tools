# -*- coding: utf-8 -*-
"""
    *This application monitors a subset of satellites with continuous data collection and is used to track the state of each satellite's solid-state recorder while its orbital position is propagated from Two-Line Elements (TLEs).*

    The application contains one :obj:`Constellation` (:obj:`Entity`) object class and one :obj:`SatStatePublisher` (:obj:`WallclockTimeIntervalPublisher`) object. The application also contains five global methods outside of these classes, which contain standardized calculations sourced from Ch. 5 of *Space Mission Analysis and Design* by Wertz and Larson.

"""

import logging
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
import numpy as np
import pandas as pd
import copy

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.entity import Entity
from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication
from nost_tools.publisher import WallclockTimeIntervalPublisher

from skyfield.api import load, wgs84, EarthSatellite

from constellation_config_files.schemas import (
    SatelliteReady,
    SatelliteAllReady,
    SatelliteState,
	FireStarted,
	FireDetected,
	FireReported,
	GroundLocation,
    LinkStart,
    LinkCharge,
    OutageReport,
    OutageRestore
)
from constellation_config_files.config import (
    PREFIX,
    NAME,
    SCALE,
    # TLES,
    FIELD_OF_REGARD,
    SSR_CAPACITY,
    CAPACITY_USED,
    INSTRUMENT_RATES,
    COST_MODE,
    FIXED_RATES
)

logging.basicConfig(level=logging.INFO)

def compute_min_elevation(altitude, field_of_regard):
    """
    Computes the minimum elevation angle required for a satellite to observe a point from current location.

    Args:
        altitude (float): Altitude (meters) above surface of the observation
        field_of_regard (float): Angular width (degrees) of observation

    Returns:
        float : min_elevation
            The minimum elevation angle (degrees) for observation
    """
    earth_equatorial_radius = 6378137.000000000
    earth_polar_radius = 6356752.314245179
    earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3

    # eta is the angular radius of the region viewable by the satellite
    sin_eta = np.sin(np.radians(field_of_regard / 2))
    # rho is the angular radius of the earth viewed by the satellite
    sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
    # epsilon is the min satellite elevation for obs (grazing angle)
    cos_epsilon = sin_eta / sin_rho
    if cos_epsilon > 1:
        return 0.0
    return np.degrees(np.arccos(cos_epsilon))


def compute_sensor_radius(altitude, min_elevation):
    """
    Computes the sensor radius for a satellite at current altitude given minimum elevation constraints.

    Args:
        altitude (float): Altitude (meters) above surface of the observation
        min_elevation (float): Minimum angle (degrees) with horizon for visibility

    Returns:
        float : sensor_radius
            The radius (meters) of the nadir pointing sensors circular view of observation
    """
    earth_equatorial_radius = 6378137.0
    earth_polar_radius = 6356752.314245179
    earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3
    # rho is the angular radius of the earth viewed by the satellite
    sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
    # eta is the nadir angle between the sub-satellite direction and the target location on the surface
    eta = np.degrees(np.arcsin(np.cos(np.radians(min_elevation)) * sin_rho))
    # calculate swath width half angle from trigonometry
    sw_HalfAngle = 90 - eta - min_elevation
    if sw_HalfAngle < 0.0:
        return 0.0
    return earth_mean_radius * np.radians(sw_HalfAngle)


def get_elevation_angle(t, sat, loc):
    """
    Returns the elevation angle (degrees) of satellite with respect to the topocentric horizon.

    Args:
        t (:obj:`Time`): Time object of skyfield.timelib module
        sat (:obj:`EarthSatellite`): Skyview EarthSatellite object from skyfield.sgp4lib module
        loc (:obj:`GeographicPosition`): Geographic location on surface specified by latitude-longitude from skyfield.toposlib module

    Returns:
        float : alt.degrees
            Elevation angle (degrees) of satellite with respect to the topocentric horizon
    """
    difference = sat - loc
    topocentric = difference.at(t)
    # NOTE: Topos uses term altitude for what we are referring to as elevation
    alt, az, distance = topocentric.altaz()
    return alt.degrees


def check_in_view(t, satellite, topos, min_elevation):
    """
    Checks if the elevation angle of the satellite with respect to the ground location is greater than the minimum elevation angle constraint.

    Args:
        t (:obj:`Time`): Time object of skyfield.timelib module
        satellite (:obj:`EarthSatellite`): Skyview EarthSatellite object from skyfield.sgp4lib module
        topos (:obj:`GeographicPosition`): Geographic location on surface specified by latitude-longitude from skyfield.toposlib module
        min_elevation (float): Minimum elevation angle (degrees) for ground to be in view of satellite, as calculated by compute_min_elevation

    Returns:
        bool : isInView
            True/False indicating visibility of ground location to satellite
    """
    isInView = False
    elevationFromFire = get_elevation_angle(t, satellite, topos)
    if elevationFromFire >= min_elevation:
        isInView = True
    return isInView


def check_in_range(t, satellite, grounds):
    """
    Checks if the satellite is in range of any of the operational ground stations.

    Args:
        t (:obj:`Time`): Time object of skyfield.timelib module
        satellite (:obj:`EarthSatellite`): Skyview EarthSatellite object from skyfield.sgp4lib module
        grounds (:obj:`DataFrame`): Dataframe of ground station locations, minimum elevation angles for communication, and operational status (T/F)

    Returns:
        bool, int :
            isInRange
                True/False indicating visibility of satellite to any operational ground station
            groundId
                groundId of the ground station currently in comm range (NOTE: If in range of two ground stations simultaneously, will return first groundId)
    """
    isInRange = False
    groundId = None
    for k, ground in grounds.iterrows():
        if ground.operational:
            groundLatLon = wgs84.latlon(ground.latitude, ground.longitude)
            satelliteElevation = get_elevation_angle(t, satellite, groundLatLon)
            if satelliteElevation >= ground.elevAngle:
                isInRange = True
                groundId = k
                break
    return isInRange, groundId


# define an entity to manage satellite updates
class Constellation(Entity):
    """
    *This object class inherits properties from the Entity object class in the NOS-T tools library*

    Args:
        cName (str): A string containing the name for the application that tracks the constituent EarthSatellites for this simulation
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        id (:obj:`list`): List of unique *int* ids for each constituent satellite
        names (:obj:`list`): List of unique *str* for each  constituent satellite (must be same length as **id**)
        ES (:obj:`list`): Optional list of :obj:`EarthSatellite` objects to be included in the simulation (NOTE: at least one of **ES** or **tles** MUST be specified, or an exception will be thrown)
        tles (:obj:`list`): Optional list of Two-Line Element *str* to be converted into :obj:`EarthSatellite` objects and included in the simulation

    Attributes:
        fires (list): List of fires with unique fireId (*int*), ignition (:obj:`datetime`), and latitude-longitude location (:obj:`GeographicPosition`) - *NOTE:* initialized as [ ]
        detect (:obj:`list`): List of detected fires with unique fireId (*int*), detected :obj:`datetime`, and name (*str*) of detecting satellite - *NOTE:* initialized as [ ]
        report (:obj:`list`): List of reported fires with unique fireId (*int*), reported :obj:`datetime`, name (*str*) of reporting satellite, and groundId (*int*) of ground station reported to - *NOTE:* initialized as [ ]
        groundTimes (:obj:`dict`): Dictionary with keys corresponding to unique satellite name and values corresponding to sequential list of ground access opportunities - *NOTE:* each value is initialized as an empty :obj:`list` and opportunities are appended chronologically
        grounds (:obj:`DataFrame`): Dataframe containing information about ground stations with unique groundId (*int*), latitude-longitude location (:obj:`GeographicPosition`), min_elevation (*float*) angle constraints, and operational status (*bool*) - *NOTE:* initialized as **None**
        satellites (:obj:`list`): List of constituent :obj:`EarthSatellite` objects - *NOTE:* must be same length as **id**
        positions (:obj:`list`): List of current latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each constituent satellite - *NOTE:* must be same length as **id**
        next_positions (:obj:`list`): List of next latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each constituent satellite - *NOTE:* must be same length as **id**
        min_elevations_fire (:obj:`list`): List of *floats* indicating current elevation angle (degrees) constraint for visibility by each satellite - *NOTE:* must be same length as **id**, updates every time step
        ssr_capacity (:obj:`list`): List of **fixed** Solid-State Recorder (SSR) capacities in Gigabits (*int*) for each constituent satellite - *NOTE:* must be same length as **id**
        capacity_used (:obj:`list`): list of values (*float*) representing current fraction of SSR capacity used for each constituent satellite, continuously updated through simulation - *NOTE:* must be same length as **id**
        instrument_rates (:obj:`list`): list of **fixed** instrument data collection rates in Gigabits/second (*float*) for each constituent satellite - *NOTE:* must be same length as **id**
        cost_mode (:obj:`list`): list of *str* representing one of three cost modes used to update cumulative costs: :obj:`discrete` (per downlink), :obj:`continuous` (fixed contract), or :obj:`both` - *NOTE:* must be same length as **id**
        fixed_rates (:obj:`list`): list of **fixed** rates of cost accumulation in dollars/second for :obj:`continuous` cost_mode for each constituent satellite - *NOTE:* must be same length as **id**, but ignored if cost_mode for corresponding satellite is :obj:`discrete`
        linkCounts (:obj:`list`): list of cumulative counts of link opportunies (*int*) for each constituent satellite - *NOTE:* must be same length as **id**, initialized as list of zeros
        linkStatus (:obj:`list`): list of states (*bool*) indicating whether or not each constituent satellite is currently in view of an available ground station - *NOTE:* must be same length as **id**, each satellite state initialized as :obj:`False`
        cumulativeCostBySat (:obj:`dict`): Dictionary with keys corresponding to unique satellite name and values corresponding to current cumulative costs in dollars (*float*) accrued by each constituent satellite, continuously updated throughout the simulation - *NOTE:* must be same length as **id**, each satellite cost initialized as zero dollars
        cumulativeCosts (float): Sum of values in cumulativeCostBySat in dollars, continuously updated throughout the simulation

    """

    ts = load.timescale()
    PROPERTY_FIRE_REPORTED = "reported"
    PROPERTY_FIRE_DETECTED = "detected"
    PROPERTY_POSITION = "position"
    PROPERTY_LINKCHARGE = "linkCharge"

    def __init__(self, cName, app, id, names, ES=None, tles=None):
        super().__init__(cName)
        self.app = app
        self.id = id
        self.names = names
        self.fires = []
        self.detect = []
        self.report = []
        self.groundTimes = {j:[] for j in self.names}
        self.grounds = None
        self.satellites = []
        if ES is not None:
            for satellite in ES:
                self.satellites.append(satellite)
        if tles is not None:
            for i, tle in enumerate(tles):
                self.satellites.append(
                    EarthSatellite(tle[0], tle[1], self.names[i], self.ts)
                )
        self.positions = self.next_positions = [None for satellite in self.satellites]
        self.min_elevations_fire = [
            compute_min_elevation(
                wgs84.subpoint(satellite.at(satellite.epoch)).elevation.m,
                FIELD_OF_REGARD[i],
            )
            for i, satellite in enumerate(self.satellites)
        ]
        self.ssr_capacity = SSR_CAPACITY # in Gigabits
        self.capacity_used = CAPACITY_USED # fraction from 0 to 1
        self.instrument_rates = INSTRUMENT_RATES # in Gigabits/second
        self.cost_mode = COST_MODE
        self.fixed_rates = FIXED_RATES
        self.linkCounts = [0 for satellite in self.satellites]
        self.linkStatus = [False for satellite in self.satellites]
        self.cumulativeCostBySat = {l:0.00 for l in self.names}
        self.cumulativeCosts = 0.00

    def initialize(self, init_time):
        """
        Activates the :obj:`Constellation` object with all constituent satellites at a specified initial scenario time

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
                "operational": pd.Series([], dtype="bool"),
                "downlinkRate": pd.Series([], dtype="float"),
                "costPerSecond": pd.Series([], dtype="float"),
                "costMode": pd.Series([], dtype="str")
            }
        )
        self.positions = self.next_positions = [
            wgs84.subpoint(satellite.at(self.ts.from_datetime(init_time)))
            for satellite in self.satellites
        ]

        for i, satellite in enumerate(self.satellites):

            self.app.send_message(
                "ready",
                SatelliteReady(
                    id=self.id[i],
                    name=self.names[i],
                    ssr_capacity=self.ssr_capacity[i]
                ).json()
            )
        self.app.send_message("allReady", SatelliteAllReady().json())

    def tick(self, time_step):
        """
        Computes the next :obj:`Constellation` state after the specified scenario duration and the next simulation scenario time

        Args:
            time_step (:obj:`timedelta`): Duration between current and next simulation scenario time
        """
        # tik = time.time()
        super().tick(time_step)
        self.next_positions = [
            wgs84.subpoint(
                satellite.at(self.ts.from_datetime(self.get_time() + time_step))
            )
            for satellite in self.satellites
        ]
        for i, satellite in enumerate(self.satellites):
            then = self.ts.from_datetime(self.get_time() + time_step)
            # First check fires
            self.min_elevations_fire[i] = compute_min_elevation(
                float(self.next_positions[i].elevation.m), FIELD_OF_REGARD[i]
            )
            for j, fire in enumerate(self.fires):
                if self.detect[j][self.names[i]] is None:
                    topos = wgs84.latlon(fire["latitude"], fire["longitude"])
                    isInView = check_in_view(
                        then, satellite, topos, self.min_elevations_fire[i]
                    )
                    if isInView:
                        self.detect[j][self.names[i]] = (
                            self.get_time() + time_step
                        )  # TODO could use event times
                        if self.detect[j]["firstDetector"] is None:
                            self.detect[j]["firstDetect"] = True
                            self.detect[j]["firstDetector"] = self.names[i]
                if (self.detect[j][self.names[i]] is not None) and (
                    self.report[j][self.names[i]] is None
                ):
                    isInRange, groundId = check_in_range(then, satellite, self.grounds)
                    if isInRange:
                        self.report[j][self.names[i]] = self.get_time() + time_step
                        if self.report[j]["firstReporter"] is None:
                            self.report[j]["firstReport"] = True
                            self.report[j]["firstReporter"] = self.names[i]
                            self.report[j]["firstReportedTo"] = groundId
            # Now check storage
            isInRange, groundId = check_in_range(then, satellite, self.grounds)
            self.capacity_used[i] = self.capacity_used[i] + ((self.instrument_rates[i]*time_step.total_seconds())/self.ssr_capacity[i])
            if self.cost_mode[i] == "continuous" or self.cost_mode[i] == "both":
                self.cumulativeCostBySat[self.names[i]] = self.cumulativeCostBySat[self.names[i]] + self.fixed_rates[i]*time_step.total_seconds()
                self.cumulativeCosts = self.cumulativeCosts + self.fixed_rates[i]*time_step.total_seconds()
            if isInRange:
                if not self.linkStatus[i]:
                    self.linkStatus[i] = True
                    self.linkCounts[i] = self.linkCounts[i] + 1
            else:
                if self.linkStatus[i]:
                    self.linkStatus[i] = False

    def tock(self):
        """
        Commits the next :obj:`Constellation` state and advances simulation scenario time

        """
        # tik = time.time()
        self.positions = self.next_positions
        for i, newly_detected_fire in enumerate(self.detect):
            if newly_detected_fire["firstDetect"]:
                detector = newly_detected_fire["firstDetector"]
                self.notify_observers(
                    self.PROPERTY_FIRE_DETECTED,
                    None,
                    {
                        "fireId": newly_detected_fire["fireId"],
                        "detected": newly_detected_fire[detector],
                        "detected_by": detector,
                    },
                )
                self.detect[i]["firstDetect"] = False
        for i, newly_reported_fire in enumerate(self.report):
            if newly_reported_fire["firstReport"]:
                reporter = newly_reported_fire["firstReporter"]
                self.notify_observers(
                    self.PROPERTY_FIRE_REPORTED,
                    None,
                    {
                        "fireId": newly_reported_fire["fireId"],
                        "reported": newly_reported_fire[reporter],
                        "reported_by": reporter,
                        "reported_to": newly_reported_fire["firstReportedTo"],
                    },
                )
            self.report[i]["firstReport"] = False
        super().tock()
        for i, satellite in enumerate(self.satellites):
            if self.cost_mode[i] == "continuous" or self.cost_mode[i] == "both":
                self.app.send_message(
                        "linkCharge",
                        LinkCharge(
                            groundId = 100,
                            satId = self.id[i],
                            satName = self.names[i],
                            linkId = 0,
                            end = self.get_time(),
                            duration = 0,
                            dataOffload = 0,
                            downlinkCost = 0,
                            cumulativeCostBySat = self.cumulativeCostBySat[self.names[i]],
                            cumulativeCosts = self.cumulativeCosts
                            ).json()
                        )
    
    
    def on_fire(self, client, userdata, message):
        """
        Callback function appends a dictionary of information for a new fire to fires :obj:`list` when message detected on the *PREFIX/fires/location* topic

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

        """
        started = FireStarted.parse_raw(message.payload)
        self.fires.append(
            {
                "fireId": started.fireId,
                "start": started.start,
                "latitude": started.latitude,
                "longitude": started.longitude,
            },
        )
        satelliteDictionary = dict.fromkeys(
            self.names
        )  # Creates dictionary where keys are satellite names and values are defaulted to NoneType
        satelliteDictionary[
            "fireId"
        ] = (
            started.fireId
        )  # Adds fireId to dictionary, which will coordinate with position of dictionary in list of dictionaries
        detectDictionary = copy.deepcopy(satelliteDictionary)
        detectDictionary["firstDetect"] = False
        detectDictionary["firstDetector"] = None
        self.detect.append(detectDictionary)
        reportDictionary = copy.deepcopy(satelliteDictionary)
        reportDictionary["firstReport"] = False
        reportDictionary["firstReporter"] = None
        reportDictionary["firstReportedTo"] = None
        self.report.append(reportDictionary)

    def on_ground(self, client, userdata, message):
        """
        Callback function appends a dictionary of information for a new ground station to grounds :obj:`list` when message detected on the *PREFIX/ground/location* topic. 
        
        Ground station information is published at beginning of simulation, and the :obj:`list` is converted to a :obj:`DataFrame` when the Constellation is initialized.

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

    def on_linkStart(self, client, userdata, message):
        """
        Callback function when message detected on the *PREFIX/ground/linkStart* topic.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

        """
        downlinkStart = LinkStart.parse_raw(message.payload)
        print(downlinkStart)
        if downlinkStart.groundId != -1:
            self.groundTimes[downlinkStart.satName].append(
                {
                    "groundId":downlinkStart.groundId,
                    "satId":downlinkStart.satId,
                    "satName":downlinkStart.satName,
                    "linkId":downlinkStart.linkId,
                    "start":downlinkStart.start,
                    "end":None,
                    "duration":None,
                    "initialData": downlinkStart.data,
                    "dataOffload":None,
                    "downlinkCost":None
                    },
            )

    def on_linkCharge(self, client, userdata, message):
       """
       Callback function when message detected on the *PREFIX/ground/linkCharge* topic.

       Args:
           client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
           userdata: User defined data of any type (not currently used)
           message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

       """
       downlinkCharge = LinkCharge.parse_raw(message.payload)
       print(downlinkCharge)
       if downlinkCharge.groundId != -1:
           self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId]["end"] = downlinkCharge.end
           self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId]["duration"] = downlinkCharge.duration
           self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId]["dataOffload"] = downlinkCharge.dataOffload
           self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId]["downlinkCost"] = downlinkCharge.downlinkCost
           self.capacity_used[downlinkCharge.satId] = self.capacity_used[downlinkCharge.satId] - (downlinkCharge.dataOffload / self.ssr_capacity[downlinkCharge.satId])
           if self.capacity_used[downlinkCharge.satId] < 0:
               self.capacity_used[downlinkCharge.satId] = 0
           self.cumulativeCostBySat[downlinkCharge.satName] = self.cumulativeCostBySat[downlinkCharge.satName] + downlinkCharge.downlinkCost
           self.cumulativeCosts = self.cumulativeCosts + downlinkCharge.downlinkCost
           
    def on_outage(self, client, userdata, message):
        """
        Callback function when message detected on the *PREFIX/outage/report* topic.
        
        Args:
           client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
           userdata: User defined data of any type (not currently used)
           message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes
            
        """
        outageReport = OutageReport.parse_raw(message.payload)
        self.grounds["operational"][outageReport.groundId] = False
        if outageReport.groundId == 11:
            for c, mode in enumerate(self.cost_mode):
                self.cost_mode[c] = "discrete"
        
    def on_restore(self, client, userdata, message):
        """
        Callback function when message detected on the *PREFIX/outage/restore* topic.
        
        Args:
           client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
           userdata: User defined data of any type (not currently used)
           message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes
            
        """
        outageRestore = OutageRestore.parse_raw(message.payload)
        self.grounds["operational"][outageRestore.groundId] = True
        if outageRestore.groundId == 11:
            for c, mode in enumerate(self.cost_mode):
                self.cost_mode[c] = "both"
               

# define a publisher to report satellite status
class SatStatePublisher(WallclockTimeIntervalPublisher):
    """
    *This object class inherits properties from the WallclockTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

    The user can optionally specify the wallclock :obj:`timedelta` between message publications and the scenario :obj:`datetime` when the first of these messages should be published.

    Args:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        constellation (:obj:`Constellation`): Constellation :obj:`Entity` object class with all constituent satellites
        time_status_step (:obj:`timedelta`): Optional duration between time status 'heartbeat' messages
        time_status_init (:obj:`datetime`): Optional scenario :obj:`datetime` for publishing the first time status 'heartbeat' message

    """

    def __init__(
        self, app, constellation, time_status_step=None, time_status_init=None
    ):
        super().__init__(app, time_status_step, time_status_init)
        self.constellation = constellation
        self.isInRange = [
            False for i, satellite in enumerate(self.constellation.satellites)
        ]

    def publish_message(self):
        """
        *Abstract publish_message method inherited from the WallclockTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

        This method sends a message to the *PREFIX/constellation/location* topic for each constituent satellite in (:obj:`Constellation`), which includes:

        Args:
            id (int): Unique id for satellite in constellation
            name (str): Unique *str* name for satellite in constellation
            latitude (float): Latitude in degrees for satellite in constellation at current scenario time
            longitude (float): Longitude in degrees for satellite in constellation at current scenario time
            altitude (float): Altitude above sea-level in meters for satellite in constellation at current scenario time
            capacity_used (float): Fraction of solid-state recorder capacity used for satellite in constellation at current scenario time
            commRange (bool): Boolean state variable indicating if satellite in constellaton is in view of a ground station at current scenario time
            groundId (int): Optional unique id for ground station in view of satellite in constellation at current scenario time (if commRange = False, the groundId = None)
            totalLinkCount (int): Unique count of downlink opportunities for satellite in constellation
            cumulativeCostBySat (float): Cumulative costs incurred for downlinks and/or fixed cost contracts for satellite in constellation at current scenario time
            time (:obj:`datetime`): Current scenario :obj:`datetime`

        """
        for i, satellite in enumerate(self.constellation.satellites):
            next_time = constellation.ts.from_datetime(
                constellation.get_time() + 60 * self.time_status_step
            )
            satSpaceTime = satellite.at(next_time)
            subpoint = wgs84.subpoint(satSpaceTime)
            sensorRadius = compute_sensor_radius(
                subpoint.elevation.m, constellation.min_elevations_fire[i]
            )
            self.isInRange[i], groundId = check_in_range(
                next_time, satellite, constellation.grounds
            )
            self.app.send_message(
                "location",
                SatelliteState(
                    id=i,
                    name=self.constellation.names[i],
                    latitude=subpoint.latitude.degrees,
                    longitude=subpoint.longitude.degrees,
                    altitude=subpoint.elevation.m,
                    radius=sensorRadius,
                    capacity_used=self.constellation.capacity_used[i]*self.constellation.ssr_capacity[i],
                    commRange=self.isInRange[i],
                    groundId=groundId,
                    totalLinkCount=self.constellation.linkCounts[i],
                    cumulativeCostBySat=self.constellation.cumulativeCostBySat[self.constellation.names[i]],
                    time=constellation.get_time(),
                ).json(),
            )


# define an observer to send fire detection events
class FireDetectedObserver(Observer):
    """
    *This object class inherits properties from the Observer object class from the observer template in the NOS-T tools library*

    Args:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions

    """

    def __init__(self, app):
        self.app = app

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class in NOS-T tools library*

        In this instance, the callback function checks for notification of the "detected" property and publishes :obj:`FireDetected` message to *PREFIX/constellation/detected* topic:

        """
        if property_name == Constellation.PROPERTY_FIRE_DETECTED:
            self.app.send_message(
                "detected",
                FireDetected(
                    fireId=new_value["fireId"],
                    detected=new_value["detected"],
                    detected_by=new_value["detected_by"],
                ).json(),
            )


# define an observer to send fire reporting events
class FireReportedObserver(Observer):
    """
    *This object class inherits properties from the Observer object class from the observer template in the NOS-T tools library*

    Args:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions

    """

    def __init__(self, app):
        self.app = app

    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class in NOS-T tools library*

        In this instance, the callback function checks for notification of the "reported" property and publishes :obj:`FireReported` message to *PREFIX/constellation/reported* topic:

        """
        if property_name == Constellation.PROPERTY_FIRE_REPORTED:
            self.app.send_message(
                "reported",
                FireReported(
                    fireId=new_value["fireId"],
                    reported=new_value["reported"],
                    reported_by=new_value["reported_by"],
                    reported_to=new_value["reported_to"],
                ).json(),
            )


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication(NAME)

    # load current TLEs for active satellites from Celestrak (NOTE: User has option to specify their own TLE instead)
    activesats_url = "https://celestrak.com/NORAD/elements/active.txt"
    activesats = load.tle_file(activesats_url, reload=True)
    by_name = {sat.name: sat for sat in activesats}

    # keys for CelesTrak TLEs used in this example, but indexes often change over time)
    names = ["SUOMI NPP", "NOAA 20"]
    ES = []
    indices = []
    for name_i, name in enumerate(names):
        ES.append(by_name[name])
        indices.append(name_i)

    # initialize the Constellation object class (in this example from EarthSatellite type) and add observers
    constellation = Constellation("constellation", app, indices, names, ES)
    constellation.add_observer(FireDetectedObserver(app))
    constellation.add_observer(FireReportedObserver(app))

    # add the Constellation entity to the application's simulator
    app.simulator.add_entity(constellation)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # add a position publisher to update satellite state every 5 seconds of wallclock time
    app.simulator.add_observer(
        SatStatePublisher(app, constellation, timedelta(seconds=1))
    )

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime(2023, 8, 7, 7, 21, tzinfo=timezone.utc),
        time_step=timedelta(seconds=1) * SCALE,
    )

    # add message callbacks
    app.add_message_callback("fire", "location", constellation.on_fire)
    app.add_message_callback("ground", "location", constellation.on_ground)
    app.add_message_callback("ground", "linkStart", constellation.on_linkStart)
    app.add_message_callback("ground", "linkCharge", constellation.on_linkCharge)
    app.add_message_callback("outage", "report", constellation.on_outage)
    app.add_message_callback("outage", "restore", constellation.on_restore)
    
    while True:
        pass