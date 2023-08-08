#!/usr/bin/env python

import json
import re
import threading
from dateutil import parser
from datetime import datetime, timedelta, timezone

from nost.observer import ExternalPublishObserver, PublishObserver, StopMessageObserver, ModeMessageObserver


def start(sim, client, prefix, data, sim_start_time, sim_stop_time, internal_step):
    """ Starts the execution.
     
    Args:
        sim (sim.simulator.Simulator): Simulator class for prefix.
        client (object): MQTT client for publishing messages.
        prefix (str): Prefix of execution topic.
        data (object): Request body.
        sim_start_time (datetime.datetime): Simulation start time.
        sim_stop_time (datetime.datetime): Simulation stop time.
        internal_step (int): Speed at which to run the execution class.

    Returns:
        bool: Whether the operation was successful.
    """
    start_time, sim_start_time, time_scaling_factor, publish_step, time_status_start_time, success = (
        datetime.now(tz=timezone.utc) + timedelta(seconds=10)), None, None, 21600, None, True
    if "startTime" in data:
        try:
            start_time = parser.parse(
                data["startTime"]).replace(tzinfo=timezone.utc)
        except Exception as e:
            print(
                "\nError: Malformed ISO-8601 datetime or missing string: 'startTime'\n")
            success = False
    try:
        sim_start_time = parser.parse(
            data["simStartTime"]).replace(tzinfo=timezone.utc)
    except Exception as e:
        print(
            "\nError: Malformed ISO-8601 datetime or missing string: 'simStartTime'\n")
        success = False
    try:
        sim_stop_time = parser.parse(
            data["simStopTime"]).replace(tzinfo=timezone.utc)
    except Exception as e:
        print(
            "\nError: Malformed ISO-8601 datetime or missing string: 'simStopTime', using 'simStopTime' from init\n")
    try:
        time_scaling_factor = float(data["timeScalingFactor"])
    except Exception as e:
        print(
            "\nError: Malformed floating-point or missing string: 'timeScalingFactor'\n")
        success = False

    try:
        publish_step = float(data["publishStep"])
    except Exception as e:
        print(
            "\nError: No 'publishStep' provided, using default value 21600 seconds (6 hours).\n")
    try:
        time_status_start_time = parser.parse(
            data["timeStatusStartTime"]).replace(tzinfo=timezone.utc)
    except Exception as e:
        print(
            "\nError: Malformed ISO-8601 datetime or missing string: 'timeStatusStartTime' or no 'timeStatusStartTime' provided, using default value of 'simStartTime'.\n")

    # Update simulator.
    if success:
        # Add observers.
        sim.add_observer(ExternalPublishObserver(
            client, prefix + "/manager/time", timedelta(seconds=publish_step), time_status_start_time))
        sim.add_observer(PublishObserver(
            client, prefix))
        # sim.add_observer(StopMessageObserver(client, prefix))
        sim.add_observer(ModeMessageObserver(client, prefix))

        # Execute execution in thread.
        threading.Thread(target=sim.execute, kwargs={
            'init_time': sim_start_time,
            'duration': sim_stop_time - sim_start_time,
            'time_step': internal_step * time_scaling_factor,
            'wallclock_epoch': start_time,
            'time_scale_factor': time_scaling_factor
        }
        ).start()
        print('\nSimulation starting at {:}\n'.format(
            sim_start_time.isoformat()))
        
        # Publish Message
        response = client.publish(
            f"{prefix}/manager/start",
            json.dumps({
                "taskingParameters": {
                    "startTime": start_time.isoformat(),
                    "simStartTime": sim_start_time.isoformat(),
                    "timeScalingFactor": time_scaling_factor
                }
            })
        )
        response.wait_for_publish()

    return success
