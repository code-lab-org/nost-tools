# -*- coding: utf-8 -*-
"""
*This application monitors a subset of satellites with continuous data collection and is used to track the state of each satellite's solid-state recorder while its orbital position is propagated from Two-Line Elements (TLEs).*

The application contains one :obj:`SatelliteStorage` (:obj:`Entity`) object class and one :obj:`SatStatePublisher` (:obj:`WallclockTimeIntervalPublisher`) object. The application also contains two global methods outside of these classes, which contain standardized calculations sourced from Ch. 5 of *Space Mission Analysis and Design* by Wertz and Larson.

*NOTE:* For example code demonstrating how an application is started up and how the :obj:`Entity` and :obj:`WallclockTimeIntervalPublisher` object classes are initialized and added to the simulator, see :ref:`FireSat+ Constellations <fireSatConstellations>`.

"""

import logging
from datetime import timedelta

import pandas as pd  # type:ignore
from satelliteStorage_config_files.schemas import (
    GroundLocation,
    LinkCharge,
    LinkStart,
    OutageReport,
    OutageRestore,
    SatelliteAllReady,
    SatelliteReady,
    SatelliteState,
)
from skyfield.api import EarthSatellite, load, wgs84  # type:ignore

from nost_tools.application_utils import ShutDownObserver
from nost_tools.configuration import ConnectionConfig
from nost_tools.entity import Entity  # type:ignore
from nost_tools.managed_application import ManagedApplication  # type:ignore
from nost_tools.publisher import WallclockTimeIntervalPublisher  # type:ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_elevation_angle(t, sat, loc):
    """
    Returns the elevation angle (degrees) of satellite with respect to the topocentric horizon

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


def check_in_range(t, satellite, grounds):
    """
    Checks if the satellite is in range of any of the operational ground stations

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
class SatelliteStorage(Entity):
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
        groundTimes (:obj:`dict`): Dictionary with keys corresponding to unique satellite name and values corresponding to sequential list of ground access opportunities - *NOTE:* each value is initialized as an empty :obj:`list` and opportunities are appended chronologically
        grounds (:obj:`DataFrame`): Dataframe containing information about ground stations with unique groundId (*int*), latitude-longitude location (:obj:`GeographicPosition`), min_elevation (*float*) angle constraints, and operational status (*bool*) - *NOTE:* initialized as **None**
        satellites (:obj:`list`): List of constituent :obj:`EarthSatellite` objects - *NOTE:* must be same length as **id**
        positions (:obj:`list`): List of current latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each constituent satellite - *NOTE:* must be same length as **id**
        next_positions (:obj:`list`): List of next latitude-longitude-altitude locations (:obj:`GeographicPosition`) of each constituent satellite - *NOTE:* must be same length as **id**
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
    PROPERTY_POSITION = "position"
    PROPERTY_LINKCHARGE = "linkCharge"

    def __init__(self, cName, app, id, names, ES=None, tles=None):
        super().__init__(cName)
        self.app = app
        self.id = id
        self.names = names
        self.groundTimes = {j: [] for j in self.names}
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
        self.ssr_capacity = config.rc.application_configuration[
            "SSR_CAPACITY"
        ]  # in Gigabits
        self.capacity_used = config.rc.application_configuration[
            "CAPACITY_USED"
        ]  # fraction from 0 to 1
        self.instrument_rates = config.rc.application_configuration[
            "INSTRUMENT_RATES"
        ]  # in Gigabits/second
        self.cost_mode = config.rc.application_configuration["COST_MODE"]
        self.fixed_rates = config.rc.application_configuration["FIXED_RATES"]
        self.linkCounts = [0 for satellite in self.satellites]
        self.linkStatus = [False for satellite in self.satellites]
        self.cumulativeCostBySat = {l: 0.00 for l in self.names}
        self.cumulativeCosts = 0.00

    def initialize(self, init_time):
        """
        Activates the :obj:`SatelliteStorage` object with all constituent satellites at a specified initial scenario time

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
                "costMode": pd.Series([], dtype="str"),
            }
        )
        self.positions = self.next_positions = [
            wgs84.subpoint(satellite.at(self.ts.from_datetime(init_time)))
            for satellite in self.satellites
        ]

        for i, satellite in enumerate(self.satellites):

            self.app.send_message(
                self.app.app_name,
                "ready",
                SatelliteReady(
                    id=self.id[i], name=self.names[i], ssr_capacity=self.ssr_capacity[i]
                ).model_dump_json(),
            )
        self.app.send_message(
            self.app.app_name, "allReady", SatelliteAllReady().model_dump_json()
        )

    def tick(self, time_step):
        """
        Computes the next :obj:`SatelliteStorage` state after the specified scenario duration and the next simulation scenario time

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
            isInRange, groundId = check_in_range(then, satellite, self.grounds)
            self.capacity_used[i] = self.capacity_used[i] + (
                (self.instrument_rates[i] * time_step.total_seconds())
                / self.ssr_capacity[i]
            )
            if self.cost_mode[i] == "continuous" or self.cost_mode[i] == "both":
                self.cumulativeCostBySat[self.names[i]] = (
                    self.cumulativeCostBySat[self.names[i]]
                    + self.fixed_rates[i] * time_step.total_seconds()
                )
                self.cumulativeCosts = (
                    self.cumulativeCosts
                    + self.fixed_rates[i] * time_step.total_seconds()
                )
            if isInRange:
                if not self.linkStatus[i]:
                    self.linkStatus[i] = True
                    self.linkCounts[i] = self.linkCounts[i] + 1
            else:
                if self.linkStatus[i]:
                    self.linkStatus[i] = False

    def tock(self):
        """
        Commits the next :obj:`SatelliteStorage` state and advances simulation scenario time

        """
        # tik = time.time()
        self.positions = self.next_positions
        super().tock()
        for i, satellite in enumerate(self.satellites):
            if self.cost_mode[i] == "continuous" or self.cost_mode[i] == "both":
                self.app.send_message(
                    self.app.app_name,
                    "linkCharge",
                    LinkCharge(
                        groundId=100,
                        satId=self.id[i],
                        satName=self.names[i],
                        linkId=0,
                        end=self.get_time(),
                        duration=0,
                        dataOffload=0,
                        downlinkCost=0,
                        cumulativeCostBySat=self.cumulativeCostBySat[self.names[i]],
                        cumulativeCosts=self.cumulativeCosts,
                    ).model_dump_json(),
                )
                logger.info("satelliteStorage.linkCharge message sent.")

    def on_ground(self, ch, method, properties, body):
        """
        Callback function appends a dictionary of information for a new ground station to grounds :obj:`list` when message detected on the *PREFIX/ground/location* topic.

        Ground station information is published at beginning of simulation, and the :obj:`list` is converted to a :obj:`DataFrame` when the Constellation is initialized.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

        """
        body = body.decode("utf-8")
        location = GroundLocation.model_validate_json(body)
        if location.groundId in self.grounds.groundId:
            self.grounds[self.grounds.groundId == location.groundId].latitude = (
                location.latitude
            )
            self.grounds[self.grounds.groundId == location.groundId].longitude = (
                location.longitude
            )
            self.grounds[self.grounds.groundId == location.groundId].elevAngle = (
                location.elevAngle
            )
            self.grounds[self.grounds.groundId == location.groundId].operational = (
                location.operational
            )
            self.grounds[self.grounds.groundId == location.groundId].downlinkRate = (
                location.downlinkRate
            )
            self.grounds[self.grounds.groundId == location.groundId].costPerSecond = (
                location.costPerSecond
            )
            logger.info(
                f"Station {location.groundId} updated at time {self.get_time()}."
            )
        else:
            location = {
                "groundId": location.groundId,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "elevAngle": location.elevAngle,
                "operational": location.operational,
                "downlinkRate": location.downlinkRate,
                "costPerSecond": location.costPerSecond,
                "costMode": location.costMode,
            }

            # Create a DataFrame from the location dictionary
            new_data = pd.DataFrame([location])

            # Concatenate the new data with the existing DataFrame
            self.grounds = pd.concat([self.grounds, new_data], ignore_index=True)

    def on_linkStart(self, ch, method, properties, body):
        """
        Callback function when message detected on the *PREFIX/ground/linkStart* topic.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

        """
        body = body.decode("utf-8")
        downlinkStart = LinkStart.model_validate_json(body)
        logger.info(f"Downlink start: {downlinkStart}")
        if downlinkStart.groundId != -1:
            self.groundTimes[downlinkStart.satName].append(
                {
                    "groundId": downlinkStart.groundId,
                    "satId": downlinkStart.satId,
                    "satName": downlinkStart.satName,
                    "linkId": downlinkStart.linkId,
                    "start": downlinkStart.start,
                    "end": None,
                    "duration": None,
                    "initialData": downlinkStart.data,
                    "dataOffload": None,
                    "downlinkCost": None,
                },
            )

    def on_linkCharge(self, ch, method, properties, body):
        """
        Callback function when message detected on the *PREFIX/ground/linkCharge* topic.

        Args:
            client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
            userdata: User defined data of any type (not currently used)
            message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

        """
        body = body.decode("utf-8")
        downlinkCharge = LinkCharge.model_validate_json(body)
        logger.info(f"Downlink charge: {downlinkCharge}")
        if downlinkCharge.groundId != -1:
            self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId][
                "end"
            ] = downlinkCharge.end
            self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId][
                "duration"
            ] = downlinkCharge.duration
            self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId][
                "dataOffload"
            ] = downlinkCharge.dataOffload
            self.groundTimes[downlinkCharge.satName][downlinkCharge.linkId][
                "downlinkCost"
            ] = downlinkCharge.downlinkCost
            self.capacity_used[downlinkCharge.satId] = self.capacity_used[
                downlinkCharge.satId
            ] - (downlinkCharge.dataOffload / self.ssr_capacity[downlinkCharge.satId])
            if self.capacity_used[downlinkCharge.satId] < 0:
                self.capacity_used[downlinkCharge.satId] = 0
            self.cumulativeCostBySat[downlinkCharge.satName] = (
                self.cumulativeCostBySat[downlinkCharge.satName]
                + downlinkCharge.downlinkCost
            )
            self.cumulativeCosts = self.cumulativeCosts + downlinkCharge.downlinkCost

    def on_outage(self, ch, method, properties, body):
        """
        Callback function when message detected on the *PREFIX/outage/report* topic.

        Args:
           client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
           userdata: User defined data of any type (not currently used)
           message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

        """
        body = body.decode("utf-8")
        outageReport = OutageReport.model_validate_json(body)
        self.grounds.loc[outageReport.groundId, "operational"] = False
        if outageReport.groundId == 11:
            for c, mode in enumerate(self.cost_mode):
                self.cost_mode[c] = "discrete"

    def on_restore(self, ch, method, properties, body):
        """
        Callback function when message detected on the *PREFIX/outage/restore* topic.

        Args:
           client (:obj:`MQTT Client`): Client that connects application to the event broker using the MQTT protocol. Includes user credentials, tls certificates, and host server-port information.
           userdata: User defined data of any type (not currently used)
           message (:obj:`message`): Contains *topic* the client subscribed to and *payload* message content as attributes

        """
        body = body.decode("utf-8")
        outageRestore = OutageRestore.model_validate_json(body)
        self.grounds.loc[outageRestore.groundId, "operational"] = True
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
        constellation (:obj:`SatelliteStorage`): SatelliteStorage :obj:`Entity` object class with all constituent satellites
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

        This method sends a message to the *PREFIX/constellation/location* topic for each constituent satellite (:obj:`SatelliteStorage`), which includes:

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
            self.isInRange[i], groundId = check_in_range(
                next_time, satellite, constellation.grounds
            )
            self.app.send_message(
                self.app.app_name,
                "location",
                SatelliteState(
                    id=i,
                    name=self.constellation.names[i],
                    latitude=subpoint.latitude.degrees,
                    longitude=subpoint.longitude.degrees,
                    altitude=subpoint.elevation.m,
                    capacity_used=self.constellation.capacity_used[i]
                    * self.constellation.ssr_capacity[i],
                    commRange=self.isInRange[i],
                    groundId=groundId,
                    totalLinkCount=self.constellation.linkCounts[i],
                    cumulativeCostBySat=self.constellation.cumulativeCostBySat[
                        self.constellation.names[i]
                    ],
                    time=constellation.get_time(),
                ).model_dump_json(),
            )


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    # Define application name
    NAME = "satelliteStorage"

    # Load config
    config = ConnectionConfig(yaml_file="downlink.yaml", app_name=NAME)

    # Create the managed application
    app = ManagedApplication(app_name=NAME)

    # Load current TLEs for active satellites from Celestrak
    activesats_url = (
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    )
    activesats = load.tle_file(
        activesats_url, filename="satelliteStorage/active.txt", reload=True
    )

    by_name = {sat.name: sat for sat in activesats}
    names = ["SUOMI NPP", "NOAA 20 (JPSS-1)"]

    ES = []
    indices = []
    for name_i, name in enumerate(names):
        ES.append(by_name[name])
        indices.append(name_i)

    # Initialize the Constellation object class (in this example from EarthSatellite type)
    constellation = SatelliteStorage("constellation", app, [0, 1], names, ES)

    # Add the Constellation entity to the application's simulator
    app.simulator.add_entity(constellation)

    # Add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # Add a position publisher to update satellite state every 5 seconds of wallclock time
    app.simulator.add_observer(
        SatStatePublisher(app, constellation, timedelta(seconds=1))
    )

    # Start up the application
    app.start_up(
        config.rc.simulation_configuration.execution_parameters.general.prefix,
        config,
    )

    # Add message callbacks
    app.add_message_callback("ground", "location", constellation.on_ground)
    app.add_message_callback("ground", "linkStart", constellation.on_linkStart)
    app.add_message_callback("ground", "linkCharge", constellation.on_linkCharge)
    app.add_message_callback("outage", "report", constellation.on_outage)
    app.add_message_callback("outage", "restore", constellation.on_restore)

    while True:
        pass
