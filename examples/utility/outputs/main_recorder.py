import time
from dotenv import dotenv_values
import pandas as pd
import datetime
import logging

from nost_tools.simulator import Mode
from nost_tools.observer import Observer
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.managed_application import ManagedApplication

from examples.utility.config import PREFIX, SCALE, SCENARIO_START, SCENARIO_END, SIM_NAME, SEED, EVENT_COUNT, EVENT_LENGTH, EVENT_START_RANGE
from examples.utility.schemas import EventStarted, EventDetected, EventReported

logging.basicConfig(level=logging.INFO)


class Recorder(Observer):


    def __init__(self, app):
        self.app = app
        self.parameters = pd.Series(
            data={"SCENARIO_START": SCENARIO_START,
                "SCENARIO_END": SCENARIO_END,
                "EVENT_COUNT": EVENT_COUNT,
                "EVENT_LENGTH": EVENT_LENGTH,
                "EVENT_START_RANGE": EVENT_START_RANGE,
                "SEED": SEED,
                "TLES": []
            }
        )
        self.events = pd.DataFrame(
            data={
                "eventId": [i for i in range(EVENT_COUNT)],
                "start": [None for _ in range(EVENT_COUNT)],
                "finish": [None for _ in range(EVENT_COUNT)],
                "detected": [[] for _ in range(EVENT_COUNT)],
                "detected_by": [[] for _ in range(EVENT_COUNT)],
                "reported": [[] for _ in range(EVENT_COUNT)],
                "reported_by": [[] for _ in range(EVENT_COUNT)],
                "reported_to": [[] for _ in range(EVENT_COUNT)],
                "latitude": [None for _ in range(EVENT_COUNT)],
                "longitude": [None for _ in range(EVENT_COUNT)],
            }
        )
        self.events.set_index("eventId", inplace=True)


    def on_change():
        pass


    def on_tles(self, client, userdata, message):
        tles=message.payload
        self.parameters["TLES"].append(tles)


    def on_event_start(self, client, userdata, message):
        start = EventStarted.parse_raw(message.payload)
        self.events["start"][start.eventId] = start.start
        self.events["finish"][start.eventId] = start.start + datetime.timedelta(hours=EVENT_LENGTH)
        self.events["latitude"][start.eventId] = start.latitude
        self.events["longitude"][start.eventId] = start.longitude


    def on_detected(self, client, userdata, message):
        detect = EventDetected.parse_raw(message.payload)
        self.events["detected"][detect.eventId].append(detect.detected)
        self.events["detected_by"][detect.eventId].append(detect.detected_by)

    
    def on_reported(self, client, userdata, message):
        report = EventReported.parse_raw(message.payload)
        self.events["reported"][report.eventId].append(report.reported)
        self.events["reported_by"][report.eventId].append(report.reported_by)
        self.events["reported_to"][report.eventId].append(report.reported_to)


if __name__ == "__main__":

    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
    USERNAME, PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]

    # set the client credentials
    config = ConnectionConfig(USERNAME, PASSWORD, HOST, PORT, True)

    # create the managed application
    app = ManagedApplication("event")

    recorder = Recorder('recorder')

    app.simulator.add_observer(ShutDownObserver(app))

    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=datetime.timedelta(seconds=10) * SCALE,
        time_status_init=SCENARIO_START,
        time_step=datetime.timedelta(seconds=0.5) * SCALE,
    )


    app.add_message_callback("event", "start", recorder.on_event_start)
    app.add_message_callback("capella", "tles", recorder.on_tles)
    app.add_message_callback("capella", "detected", recorder.on_detected)
    app.add_message_callback("capella", "reported", recorder.on_reported)
    app.add_message_callback("planet", "tles", recorder.on_tles)
    app.add_message_callback("planet", "detected", recorder.on_detected)
    app.add_message_callback("planet", "reported", recorder.on_reported)

    while not app.simulator.get_mode() == Mode.TERMINATED:
        time.sleep(1)

    print(recorder.parameters)
    recorder.parameters.to_csv(f"outputs/{SIM_NAME}.csv", mode="w")

    with open(f"outputs/{SIM_NAME}.csv", "a") as f: f.write("\n\n\n")

    print(recorder.events)
    recorder.events.to_csv(f"outputs/{SIM_NAME}.csv", mode="a")