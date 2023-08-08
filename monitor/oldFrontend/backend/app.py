#!/usr/bin/env python

import json
from datetime import datetime, timedelta, timezone
from flask import Flask, request, send_from_directory
import paho.mqtt.client as mqtt
import ntplib
import time

from nost import Simulator, Mode
from nost import HOST, PORT, USERNAME, PASSWORD
from nost import init, start, stop, update, test_script
from nost import Middleware, get_wallclock_offset

app = Flask(__name__, static_url_path='')
app.wsgi_app = Middleware(app.wsgi_app)
last_nist_query = None


# Defining state and constant variables
sim_start_time = None
sim_stop_time = None
PUBLISH_STEP = timedelta(milliseconds=10)
OFFSET = timedelta(seconds=0)

# Establishing MQTT connection
CLIENT = mqtt.Client()
CLIENT.username_pw_set(username=USERNAME, password=PASSWORD)
CLIENT.tls_set()
CLIENT.connect(HOST, PORT, 60)
CLIENT.loop_start()

# Instantiating Simulator
SIMULATORS = {}
TEST_SCRIPTS = {}


def get_simulator(prefix):
    if prefix in SIMULATORS:
        return SIMULATORS[prefix]
    else:
        SIM = Simulator(wallclock_offset=OFFSET)
        SIMULATORS[prefix] = SIM
        return SIMULATORS[prefix]


def get_test_script(prefix):
    if prefix in TEST_SCRIPTS:
        return TEST_SCRIPTS[prefix]
    else:
        return None


@app.route('/docs/<path:path>')
def docs(path):
    return send_from_directory('docs/_build/html', path)


@app.route('/state/<prefix>', methods=["GET"])
def state_route(prefix):
    SIM = get_simulator(prefix)
    return SIM.get_mode().name


@app.route('/init/<prefix>', methods=["POST"])
def init_route(prefix):
    SIM = get_simulator(prefix)
    if SIM.get_mode() == Mode.INITIALIZING:
        return "\nError: Execution is initializing\n"
    elif SIM.get_mode() == Mode.EXECUTING:
        return "\nError: Execution is executing\n"
    elif SIM.get_mode() == Mode.TERMINATING:
        return "\nError: Execution is terminating\n"
    else:
        data = request.json
        global sim_start_time, sim_stop_time
        result, sim_start, sim_stop = init(CLIENT, prefix, data)
        if result:
            sim_start_time, sim_stop_time = sim_start, sim_stop
            return "Execution is initialized"
        else:
            return "Failed initialization, check message syntax"


@app.route('/start/<prefix>', methods=["POST"])
def start_route(prefix):
    SIM = get_simulator(prefix)
    if SIM.get_mode() == Mode.EXECUTING:
        return "\nError: Execution is executing\n"
    elif SIM.get_mode() == Mode.TERMINATING:
        return "\nError: Execution is terminating\n"
    elif sim_stop_time is None:
        return "\nError: Execution is not initialized\n"
    else:
        data = request.json
        result = start(SIM, CLIENT, prefix, data, sim_start_time,
                       sim_stop_time, PUBLISH_STEP)
        if result:
            return "Execution set to start"
        else:
            return "Failed start, check message syntax"


@app.route('/stop/<prefix>', methods=["POST"])
def stop_route(prefix):
    SIM = get_simulator(prefix)
    if SIM.get_mode() != Mode.EXECUTING:
        return "\nError: Execution is not executing\n"
    else:
        data = request.json
        result = stop(SIM, CLIENT, prefix, data)
        if result:
            return "Execution set to stop"
        else:
            return "Failed stop, check message syntax"


@app.route('/update/<prefix>', methods=["POST"])
def update_route(prefix):
    SIM = get_simulator(prefix)
    if SIM.get_mode() != Mode.EXECUTING:
        return "\nError: Simulation is not executing\n"
    else:
        data = request.json
        result = update(SIM, CLIENT, prefix, data)
        if result:
            return "Simulation set to update"
        else:
            return "Failed update, check message syntax"


@app.route('/testScript/<prefix>', methods=["POST"])
def test_script_route(prefix):
    SIM = get_simulator(prefix)
    if SIM.get_mode() == Mode.INITIALIZING:
        return "\nError: Execution is initializing\n"
    elif SIM.get_mode() == Mode.EXECUTING:
        return "\nError: Execution is executing\n"
    elif SIM.get_mode() == Mode.TERMINATING:
        return "\nError: Execution is terminating\n"
    else:
        data = request.json
        result, TestScript = test_script(SIM, CLIENT, prefix, data, sim_start_time,
                                         sim_stop_time, PUBLISH_STEP)
        TEST_SCRIPTS[prefix] = TestScript
        if result:
            return "Test script loaded"
        else:
            return "Failed loading test script, check message syntax"


@app.route('/testScriptCancel/<prefix>', methods=["GET"])
def test_script_cancel_route(prefix):
    SIM = get_simulator(prefix)
    TEST_SCRIPT = get_test_script(prefix)
    if TEST_SCRIPT is not None:
        TEST_SCRIPTS.pop(prefix, None)
        SIM.remove_observer(TEST_SCRIPT)
        return "Test Script Observer Removed"
    else:
        return "No Test Script Observer"


if __name__ == '__main__':
    _ = get_simulator("nost")
    OFFSET, last_nist_query = get_wallclock_offset(last_nist_query)
    app.run(debug=True, host='0.0.0.0')
