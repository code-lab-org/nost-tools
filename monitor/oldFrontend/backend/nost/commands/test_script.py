#!/usr/bin/env python

import json
import re
import threading
import time
from dateutil import parser
from datetime import datetime, timezone, timedelta

from nost.observer import ExternalPublishObserver, PublishObserver, TestScriptObserver
from nost.commands import init, start


def test_script(sim, client, prefix, data, sim_start_time, sim_stop_time, internal_step):
    """ Starts a test script controlled execution.
     
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
        nost.observer.TestScriptObserver: Reference to TestScriptObserver.
    """

    TestScript = TestScriptObserver(sim, client, prefix, data["updates"])

    # Adding observer
    sim.add_observer(TestScript)

    # Init
    print("Sending init message")
    result, sim_start, sim_stop = init(client, prefix, data["init"])
    sim_start_time, sim_stop_time = sim_start, sim_stop
    if not result:
        return False

    print("Sleeping for {} seconds".format(data["init"]["delay"]))
    time.sleep(data["init"]["delay"])

    # Start
    print("Sending start message")
    result = start(
        sim, client, prefix, data["start"], sim_start_time, sim_stop_time, internal_step)
    if not result:
        return False, TestScript

    return True, TestScript
