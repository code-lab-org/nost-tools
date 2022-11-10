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

pd.options.mode.chained_assignment = None

from nost_tools.simulator import Mode
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication

from examples.utility.schemas import EventState, EventStarted, EventDetected, EventReported, EventFinished
from examples.utility.config import PREFIX, SCALE, SCENARIO_START, SCENARIO_END, SIM_NAME, SEED, EVENT_COUNT, EVENT_LENGTH, EVENT_START_RANGE


logging.basicConfig(level=logging.INFO)


# define an observer to manage event updates and record to a dataframe events
class Environment(Observer):
    """
    *The Environment object class inherits properties from the Observer object class in the NOS-T tools library*

    Attributes:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        events (:obj:`DataFrame`): Dataframe of scenario scheduled events including eventId (*int*), event ignition (:obj:`datetime`), and fire latitude-longitude location (:obj:`GeographicPosition`)
    """

    def __init__(self, app, event_count, event_length, event_start_range, scenario_start, seed):
        self.app = app
        self.event_count = event_count
        self.event_length = event_length
        self.event_start_range = event_start_range
        self.scenario_start = scenario_start
        self.seed = seed

        self.events = self.generate_events()


    def generate_events(self):

        # Checks if a seed is passed when the script is ran, if not generate a random one
        random.seed(self.seed)

        # Creates list of IDs
        eventIds = [id for id in range(0, self.event_count)]

        # Initalizes event attribute lists
        eventStarts = []
        eventFinishes = []
        eventLats = []
        eventLongs = []

        # Creates random values for event start times and locations, creates finish times at a fixed interval after start
        for event in range(0, self.event_count):
            eventStart = self.scenario_start + datetime.timedelta(minutes=random.randrange(self.event_start_range[0]*60, self.event_start_range[1]*60))
            eventStarts.append(eventStart)
            eventFinishes.append(eventStart + datetime.timedelta(hours=self.event_length))
            eventLats.append(random.randrange(-60, 60))
            eventLongs.append(random.randrange(-180, 180))
        
        # Read the csv file and convert to a DataFrame with initial column defining the index
        events = pd.DataFrame(
            data={
                "eventId": eventIds,
                "started": [False for _ in eventIds],
                "start": eventStarts,
                "finish": eventFinishes,
                "latitude": eventLats,
                "longitude": eventLongs,
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
            new_events = self.events[
                (self.events.start <= new_value) & (self.events.started == False)
            ]
            for i, event in new_events.iterrows():
                # print(f"eventId: {event.eventId}")
                self.events["started"][i] = True
                self.app.send_message(
                    "start",
                    EventStarted(
                        eventId=i,
                        start=event.start,
                        latitude=event.latitude,
                        longitude=event.longitude,
                    ).json(),
                )

            finished_events = self.events[
                (self.events.finish <= new_value) & (self.events.finish > old_value)
            ]

            for i, event in finished_events.iterrows():
                # print(f"eventId: {event.eventId}")
                self.app.send_message(
                    "finish",
                    EventFinished(
                        eventId=i
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
    environment = Environment(app, EVENT_COUNT, EVENT_LENGTH, EVENT_START_RANGE, SCENARIO_START, SEED)

    # add the environment observer to monitor for event status events
    app.simulator.add_observer(environment)

    # add a shutdown observer to shut down after a single test case
    app.simulator.add_observer(ShutDownObserver(app))

    # start up the application on PREFIX, publish time status every 10 seconds of wallclock time
    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=datetime.timedelta(seconds=10) * SCALE,
        time_status_init=SCENARIO_START,
        time_step=datetime.timedelta(seconds=0.5) * SCALE,
    )

    # Ensures the application hangs until the simulation is terminated, to allow background threads to run
    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(1)

    print(environment.events)