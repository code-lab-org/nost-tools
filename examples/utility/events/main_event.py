# -*- coding: utf-8 -*-
"""
    *This application demonstrates a simulation of a schedule of fires given geospatial locations and specified datetimes (at one minute resolution)*
    
    The application contains a single :obj:`Environment` class which listens to the time status published by the manager application and publishes fire information at the specified ignition :obj:`datetime`. The application also contains callback messages that updates :obj:`datetime` in the fires :obj:`DataFrame` for each of ignition (including latitude-longitude :obj:`GeographicPosition`), detection, and reporting.

"""

import time
import random
import sys
import logging
import datetime
from dotenv import dotenv_values
import pandas as pd
from pytz import timezone
from skyfield import almanac
from skyfield.api import N, W, wgs84, load

pd.options.mode.chained_assignment = None

from nost_tools.simulator import Mode
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication

from examples.utility.schemas import EventState, EventStarted, EventDetected, EventReported, EventDayChange, EventFinished
from examples.utility.config import PARAMETERS


logging.basicConfig(level=logging.INFO)


# define an observer to manage event updates and record to a dataframe events
class Environment(Observer):
    """
    *The Environment object class inherits properties from the Observer object class in the NOS-T tools library*

    Attributes:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        events (:obj:`DataFrame`): Dataframe of scenario scheduled events including eventId (*int*), event ignition (:obj:`datetime`), and fire latitude-longitude location (:obj:`GeographicPosition`)
    """

    def __init__(self, app, event_count, event_length, event_start_range, scenario_start, scenario_length, seed):
        self.app = app
        self.event_count = event_count
        self.event_length = event_length
        self.event_start_range = event_start_range
        self.scenario_start = scenario_start
        self.scenario_length = scenario_length
        self.seed = seed

        self.events = self.generate_events()

    def generate_events(self):

        ts = load.timescale()
        eph = load("de421.bsp")

        # Checks if a seed is passed when the script is ran, if not generate a random one
        random.seed(self.seed)

        # Creates list of IDs
        eventIds = [id for id in range(0, int(self.event_count))]

        # Initalizes event attribute lists
        eventStarts = []
        eventFinishes = []
        eventLats = []
        eventLongs = []
        eventSunriseSunsets = []
        eventIsDays = []

        # Creates random values for event start times and locations, creates finish times at a fixed interval after start
        for eventId in eventIds:
            eventStart = self.scenario_start + datetime.timedelta(minutes=random.randrange(self.event_start_range[0]*60, self.event_start_range[1]*60))
            eventStarts.append(eventStart)

            eventFinishes.append(eventStart + datetime.timedelta(hours=self.event_length))

            eventLat = random.randrange(-60, 60)
            eventLats.append(eventLat)

            eventLong = random.randrange(-180, 180)
            eventLongs.append(eventLong)

            day_change_range_start = max(
                    PARAMETERS["SCENARIO_START"], 
                    eventStart
                )
            
            day_change_range_end = min(
                    PARAMETERS["SCENARIO_START"]+datetime.timedelta(hours=PARAMETERS["SCENARIO_LENGTH"]), 
                    eventStart + datetime.timedelta(hours=self.event_length))

            print(f'{eventId}: day_change_range_start: {day_change_range_start} day_change_range_end: {day_change_range_end}')

            t0, y0 = almanac.find_discrete(
                ts.from_datetime(day_change_range_start - datetime.timedelta(hours=24)),
                ts.from_datetime(day_change_range_start),
                almanac.sunrise_sunset(eph, wgs84.latlon(eventLat, eventLong)
                )
            )

            t, y = almanac.find_discrete(
                ts.from_datetime(day_change_range_start),
                ts.from_datetime(day_change_range_end),
                almanac.sunrise_sunset(eph, wgs84.latlon(eventLat, eventLong)
                )
            )

            eventSunriseSunset = [list(t.utc_datetime()), [int(y0[-1])] + [int(num) for num in y]]
            print(eventSunriseSunset)
            eventIsDay = eventSunriseSunset[1].pop(0)
            eventIsDays.append(eventIsDay)
            eventSunriseSunsets.append(eventSunriseSunset)

        events = pd.DataFrame(
            data={
                "eventId": eventIds,
                "started": [False for _ in eventIds],
                "start": eventStarts,
                "finish": eventFinishes,
                "latitude": eventLats,
                "longitude": eventLongs,
                "sunriseSunset": eventSunriseSunsets,
                "isDay": eventIsDays
            }
        )
        events.set_index("eventId", inplace=True)

        return events


    def on_change(self, source, property_name, old_value, new_value):
        """
        *Standard on_change callback function format inherited from Observer object class*

        In this instance, the callback function checks the simulation :obj:`datetime` against each scheduled event ignition :obj:`datetime` for the scenario. If past the scheduled start of an event, a :obj:`EventStarted` message is sent to *PREFIX/event/location*:


        """
        if property_name == "time":
            for eventId, event in self.events.iterrows():
                print(eventId, ':', event["sunriseSunset"])
                if event["start"] <= new_value and event["started"] == False:
                    self.events["started"][eventId] = True
                    self.app.send_message(
                        "start",
                        EventStarted(
                            eventId=eventId,
                            start=event["start"],
                            latitude=event['latitude'],
                            longitude=event['longitude'],
                            isDay=event['isDay']
                        ).json(),
                    )

                try:
                    if event["sunriseSunset"][0][0] <= new_value:
                        print(f"pop: {self.events['sunriseSunset'][eventId][0][0]}")   
                        self.events["sunriseSunset"][eventId][0].pop(0)
                        isDay = self.events["sunriseSunset"][eventId][1].pop(0)
                        print(f"pop: {isDay}")  
                        self.events["isDay"][eventId] = int(isDay)

                        self.app.send_message(
                            "dayChange",
                            EventDayChange(
                                eventId=eventId,
                                isDay=int(isDay)
                            ).json(),
                        )
                except:
                    pass

                if event["finish"] <= new_value and event["finish"] > old_value:
                    print("finish")
                    self.app.send_message(
                        "finish",
                        EventFinished(
                            eventId=eventId
                        ).json(),
                    )


if __name__ == "__main__":

    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication("event")

    # Create environment that generates events
    environment = Environment(app, 
        PARAMETERS['EVENT_COUNT'], 
        PARAMETERS['EVENT_LENGTH'], 
        PARAMETERS['EVENT_START_RANGE'], 
        PARAMETERS['SCENARIO_START'], 
        PARAMETERS['SCENARIO_LENGTH'],
        PARAMETERS['SEED'])

    # add the environment observer to monitor for event status events
    app.simulator.add_observer(environment)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PARAMETERS['PREFIX'],
        config,
        True,
        time_status_step=datetime.timedelta(seconds=10) * PARAMETERS['SCALE'],
        time_status_init=PARAMETERS['SCENARIO_START'],
        time_step=datetime.timedelta(seconds=0.5) * PARAMETERS['SCALE'],
    )

    # Ensures the application hangs until the simulation is terminated, to allow background threads to run
    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(1)

    print(environment.events.to_string())