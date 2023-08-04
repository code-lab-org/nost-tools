import logging
import os

from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from nost_tools.manager import Manager
from nost_tools.application_utils import ConnectionConfig
from pydantic import ValidationError

from schemas import InitRequest, StartRequest, StopRequest, UpdateRequest, ExecuteRequest

# configure logging
logging.basicConfig(level=logging.INFO)

# create application
app = Flask(__name__)

# configure CORS middleware
#CORS(app)

# load environment variables from the .env file 
load_dotenv()
config = ConnectionConfig(
    os.getenv("CLIENT_USERNAME", "manager"), 
    os.getenv("CLIENT_PASSWORD"), 
    os.getenv("BROKER_HOST"), 
    int(os.getenv("BROKER_PORT", 8883)), 
    True
)

print(config.username, config.password, config.host, config.port)

MANAGERS = {}

def get_manager(prefix):
    if prefix in MANAGERS:
        return MANAGERS[prefix]
    else:
        MANAGERS[prefix] = Manager()
        MANAGERS[prefix].start_up(prefix, config, True)
        return MANAGERS[prefix]

@app.route("/status/<prefix>", methods=["GET"])
def get_simulation_mode(prefix: str):
    return get_manager(prefix).simulator.get_mode()

@app.route("/init/<prefix>", methods=["POST"])
def init(prefix: str):
    try:
        req = InitRequest.parse_obj(request.get_json())
    except ValidationError as err:
        return err, 400
    get_manager(prefix).init(
        req.sim_start_time,
        req.sim_stop_time,
        req.required_apps
    )
    return "Success", 200

@app.route("/start/<prefix>", methods=["POST"])
def start(prefix: str):
    try:
        req = StartRequest.parse_obj(request.get_json())
    except ValidationError as err:
        return err, 400
    get_manager(prefix).start(
        req.sim_start_time,
        req.sim_stop_time,
        req.start_time,
        req.time_step,
        req.time_scale_factor,
        req.time_status_step,
        req.time_status_init
    )
    return "Success", 200

@app.route("/stop/<prefix>", methods=["POST"])
def stop(prefix: str):
    try:
        req = StopRequest.parse_obj(request.get_json())
    except ValidationError as err:
        return err, 400
    get_manager(prefix).stop(
        req.sim_stop_time
    )
    return "Success", 200

@app.route("/update/<prefix>", methods=["POST"])
def update(prefix: str):
    try:
        req = UpdateRequest.parse_obj(request.get_json())
    except ValidationError as err:
        return err, 400
    get_manager(prefix).update(
        req.time_scale_factor,
        req.sim_update_time
    )
    return "Success", 200

@app.route("/testScript/<prefix>", methods=["POST"])
def execute_test_plan(prefix: str):
    try:
        req = ExecuteRequest.parse_obj(request.get_json())
    except ValidationError as err:
        return err, 400
    get_manager(prefix).execute_test_plan(
        req.sim_start_time,
        req.sim_stop_time,
        req.start_time,
        req.time_step,
        req.time_scale_factor,
        [u.to_manager_format() for u in req.time_scale_updates],
        req.time_status_step,
        req.time_status_init,
        req.command_lead,
        req.required_apps,
        req.init_retry_delay_s,
        req.init_max_retry
    )
    return "Success", 200

if __name__ == "__main__":
    app.run(port=3000)