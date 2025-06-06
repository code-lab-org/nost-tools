# -*- coding: utf-8 -*-
"""
*Unmanaged application that monitors heartbeat message time delays*

Application listens for *status/time* topics of specified applications and records reported wallclock time for comparison against own wallclock time when message subscription received from the broker.

"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from os.path import exists

import ntplib
import numpy as np
import pandas as pd
import pika
from delay_config_files.config import APPS, PREFIX
from dotenv import dotenv_values
from scipy import stats

logging.basicConfig(level=logging.INFO)


def query_nist(host="pool.ntp.org", retry_delay_s=5, max_retry=5):
    """
    Contacts an NTP server to determine the system clock offset, which is necessary for synchronizing and accurately recording time_status message delays.

    Args:
        host (str) : the NTP host (default: 'pool.ntp.org').
        retry_delay_s (int) : the number of seconds to wait before retrying.
        max_retry (int) : the maximum number of retries allowed.

    Returns:
        :obj:`timedelta` : offset
            time duration measuring delay between system wallclock and NTP server reference

    """
    for i in range(max_retry):
        try:
            logging.info(f"Contacting {host} to retrieve wallclock offset.")
            response = ntplib.NTPClient().request(host, version=3, timeout=2)
            offset = timedelta(seconds=response.offset)
            logging.info(
                f"Wallclock offset updated to {offset}.\nWaiting for manager start command."
            )
            return offset
        except ntplib.NTPException:
            logging.warning(
                f"Could not connect to {host}, attempt #{i+1}/{max_retry} in {retry_delay_s} s."
            )
            time.sleep(retry_delay_s)


def post_processing(
    names, msg_dictionaries, msg_periodicity=None, msg_size=None, wallclock_offset=None
):
    """
    At end of simulation, calculates time difference between reported wallclock publish :obj:`datetime` and system wallclock receipt :obj:`datetime` (with wallclock_offset from NTP server accounted for) in microseconds for *each* time status message. Converts final :obj:`list` of these measured time delays into a :obj:`DataFrame` and calculates summary statistics for mean, median, mode, standard deviation, and skew of time delay distributions.

    Args:
        names (list): list of names (*str*) of applications that were monitored for delays
        msg_dictionaries (list): list of dictionaries with common keys representing each messages time delay information
        msg_periodicity (float): duration between successive time status messages (typically reported by application at beginning of simulation)
        msg_size (int): number of characters in the message where one *char* equals one byte (typically reported by application at beginning of simulation)
        wallclock_offset (:obj:`timedelta`): recorded system offset as determined from request to NTP server

    Returns:
        :obj:`dict`, :obj:`dict` :
            app_df_dict
                :obj:`dict` with ``key:value`` pair defined by application names (*str*): :obj:`DataFrame` of message time delays for corresponding application
            stats_df_dict
                :obj:`dict` with ``key:value`` pair defined by application names (*str*): summary statistics for delay messages for corresponding application
    """
    app_df_dict = {}
    stats_df_dict = {}
    for i, application in enumerate(names):
        app_df_dict[application] = pd.DataFrame(msg_dictionaries[application])
        app_df_dict[application].set_index("msgId", inplace=True)
        app_df_dict[application]["timeStamp"] = pd.to_datetime(
            app_df_dict[application]["timeStamp"]
        )
        app_df_dict[application]["sysTimeNST"] = pd.to_datetime(
            app_df_dict[application]["sysTimeNST"]
        )
        app_df_dict[application]["timeDiff (s)"] = (
            app_df_dict[application]["sysTimeNST"]
            - app_df_dict[application]["timeStamp"]
        ).dt.seconds
        app_df_dict[application]["timeDiff (microseconds)"] = (
            app_df_dict[application]["sysTimeNST"]
            - app_df_dict[application]["timeStamp"]
        ).dt.microseconds
        app_df_dict[application]["timeDiff total (ms)"] = app_df_dict[application][
            "timeDiff (s)"
        ] * 1000.0 + (app_df_dict[application]["timeDiff (microseconds)"] / 1000.0)
        app_df_dict[application].loc[
            app_df_dict[application]["timeDiff (s)"] >= 86399, "timeDiff total (ms)"
        ] = (app_df_dict[application]["timeDiff total (ms)"] - 86400000.0)
        app_df_dict[application].loc[
            app_df_dict[application]["timeDiff (s)"] >= 86399, "timeDiff (microseconds)"
        ] = app_df_dict[application]["timeDiff total (ms)"]
        app_df_dict[application].loc[
            app_df_dict[application]["timeDiff (s)"] >= 86399, "timeDiff (s)"
        ] = 0

        # sns.displot(data=app_df_dict[application],x='timeDiff total (ms)')
        # sns.lineplot(data=app_df_dict[application],x='msgId',y='timeDiff total (ms)')

        statsDelay = {
            "# of messages": len(app_df_dict[application]["timeDiff total (ms)"]),
            "simulation duration (s)": len(
                app_df_dict[application]["timeDiff total (ms)"]
            )
            * msg_periodicity,
            "message periodicity (s)": msg_periodicity,
            "message size (bytes)": msg_size,
            "wallclock offset": wallclock_offset,
            "mean (ms)": np.mean(app_df_dict[application]["timeDiff total (ms)"]),
            "median (ms)": np.median(app_df_dict[application]["timeDiff total (ms)"]),
            "mode (ms)": stats.mstats.mode(
                app_df_dict[application]["timeDiff total (ms)"]
            )[0][0],
            "standard deviation (ms)": np.std(
                app_df_dict[application]["timeDiff total (ms)"]
            ),
            "skewness": stats.skew(app_df_dict[application]["timeDiff total (ms)"]),
        }
        stats_df_dict[application] = pd.DataFrame([statsDelay])
    return app_df_dict, stats_df_dict


class HeartbeatDelayRecorder:
    """
    Records delays in time_status messages between published timestamp and system clock receipt time for subscribed message from event broker

    Args:
        names (list): list of names (*str*) for each application to be monitored

    Attributes:
        msg_dictionaries (:obj:`dict`): initialized dictionary with keys corresponding to ``names`` and empty lists for values
        sim_end_time (:obj:`datetime`): :obj:`datetime` corresponding to end of simulation (initialized to `None`), to be updated on receipt of stop message from manager
        _wallclock_offset (:obj:`timedelta`): ``query_nist`` method called when class initialized, returning :obj:`timedelta` between system wallclock and NTP server reference
        msg_periodicity (float): duration between successive time status messages (initialized to `None`), to be updated on receipt of heartbeat settings message
        msg_size (int):  number of characters in the message where one *char* equals one byte (initialized to `None`), to be updated on receipt of heartbeat settings message

    """

    def __init__(self, names):
        self.names = names  # names of applications to be monitored for delays
        self.msg_dictionaries = dict(zip(self.names, ([] for _ in self.names)))
        self.sim_end_time = None
        self._wallclock_offset = query_nist()
        self.msg_periodicity = None
        self.msg_size = None
        self.channel = None  # Reference to the Pika channel

    def get_wallclock_time(self):
        """
        Returns the current wallclock time based on standardized NIST time.

        Returns:
            :obj:`datetime`: current wallclock time, accounting for offset.
        """
        return datetime.now(tz=timezone.utc) + self._wallclock_offset

    def on_message(self, channel, method, properties, body):
        """
        Callback function for Pika message consumption
        """
        topic = method.routing_key
        msg_payload = body

        data = json.loads(msg_payload.decode("utf-8"))

        if topic == f"{PREFIX}.manager.start":
            print("Manager initiated simulation")
        elif topic == f"{PREFIX}.manager.stop":
            print("Manager published stop message")
            self.sim_end_time = pd.to_datetime(data["taskingParameters"]["simStopTime"])
        elif topic == f"{PREFIX}.heartbeat.settings":
            print("Heartbeat application settings detected")
            self.msg_periodicity = float(data["periodicity"])
            self.msg_size = float(data["messageBytes"])

        for i, application in enumerate(self.names):
            if topic == f"{PREFIX}.status.{application}.time":
                msgId = len(self.msg_dictionaries[application])
                timeStamp = pd.to_datetime(data["properties"]["time"])
                if self.sim_end_time != None:
                    scenarioTime = pd.to_datetime(data["properties"]["simTime"])
                    if scenarioTime >= self.sim_end_time:
                        if self.channel:
                            self.channel.stop_consuming()
                        print(
                            "Simulation has passed the specified end time. Beginning post-processing:"
                        )
                        self.app_df_dict, self.stats_df_dict = post_processing(
                            self.names,
                            self.msg_dictionaries,
                            self.msg_periodicity,
                            self.msg_size,
                            self._wallclock_offset,
                        )

                        if not os.path.exists("delay_data_collection"):
                            os.makedirs("delay_data_collection")

                        self.app_df_dict["heartbeat"].to_csv(
                            f"delay_data_collection/logs_msgFreq_{self.msg_periodicity}_msgSize_{self.msg_size}.csv"
                        )
                        if exists("delay_data_collection/doeStats.csv"):
                            self.stats_df_dict["heartbeat"].to_csv(
                                "delay_data_collection/doeStats.csv",
                                mode="a",
                                index=False,
                                header=False,
                            )
                        else:
                            self.stats_df_dict["heartbeat"].to_csv(
                                "delay_data_collection/doeStats.csv",
                                mode="a",
                                index=False,
                                header=True,
                            )

                        print("Post-processing complete, exiting application.")
                        sys.exit()
                msgSize = len(msg_payload)
                self.msg_dictionaries[application].append(
                    {
                        "msgId": msgId,
                        "timeStamp": timeStamp,
                        "sysTimeNST": self.get_wallclock_time(),
                        "msgSize": msgSize,
                    }
                )


if __name__ == "__main__":
    # initialize the HeartbeatDelayRecorder with list of application names (APPS) from delay_config_files/config.py
    hbdr = HeartbeatDelayRecorder(APPS)

    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST = credentials["HOST"]
    PORT = credentials["PORT"]
    USERNAME = credentials["USERNAME"]
    PASSWORD = credentials["PASSWORD"]

    # Set up RabbitMQ connection
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    parameters = pika.ConnectionParameters(
        host=HOST,
        credentials=credentials,
        port=PORT,
    )

    connection = pika.BlockingConnection(parameters)
    channel = hbdr.channel = connection.channel()

    # Declare exchange - assuming a topic exchange
    exchange_name = PREFIX
    channel.exchange_declare(
        exchange=exchange_name, exchange_type="topic", durable=True, auto_delete=True
    )

    # Create a queue for this consumer
    result = channel.queue_declare("", exclusive=True)
    queue_name = result.method.queue

    # Binding patterns
    routing_keys = [
        f"{PREFIX}.manager.start",
        f"{PREFIX}.manager.stop",
        f"{PREFIX}.heartbeat.settings",
    ]

    # Add application specific bindings
    for application in hbdr.names:
        routing_keys.append(f"{PREFIX}.status.{application}.time")

    # Bind queue to all routing keys
    for routing_key in routing_keys:
        channel.queue_bind(
            exchange=exchange_name, queue=queue_name, routing_key=routing_key
        )

    # Set up consumer
    channel.basic_consume(
        queue=queue_name, on_message_callback=hbdr.on_message, auto_ack=True
    )

    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()
