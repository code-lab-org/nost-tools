import logging
import os
from typing import Union

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nost_tools.manager import Manager
from nost_tools.application_utils import ConnectionConfig

from schemas import InitRequest, StartRequest, StopRequest, UpdateRequest, ExecuteRequest

# configure logging
logging.basicConfig(level=logging.INFO)

# create application
app = FastAPI()

# configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# load environment variables from the .env file 
load_dotenv()
config = ConnectionConfig(
    os.getenv("CLIENT_USERNAME", "manager"), 
    os.getenv("CLIENT_PASSWORD"), 
    os.getenv("BROKER_HOST"), 
    int(os.getenv("BROKER_PORT", 8883)), 
    True
)

MANAGERS = {}

def get_manager(prefix):
    if prefix in MANAGERS:
        return MANAGERS[prefix]
    else:
        MANAGERS[prefix] = Manager()
        MANAGERS[prefix].start_up(prefix, config, True)
        return MANAGERS[prefix]

@app.get("/status/{prefix}")
def get_simulation_mode(prefix: str):
    return get_manager(prefix).simulator.get_mode()

@app.post("/init/{prefix}")
def init(prefix: str, request: InitRequest):
    get_manager(prefix).init(
        request.sim_start_time,
        request.sim_stop_time,
        request.required_apps
    )

@app.post("/start/{prefix}")
def start(prefix: str, request: StartRequest):
    get_manager(prefix).start(
        request.sim_start_time,
        request.sim_stop_time,
        request.start_time,
        request.time_step,
        request.time_scale_factor,
        request.time_status_step,
        request.time_status_init
    )

@app.post("/stop/{prefix}")
def stop(prefix: str, request: StopRequest):
    get_manager(prefix).stop(
        request.sim_stop_time
    )

@app.post("/update/{prefix}")
def update(prefix: str, request: UpdateRequest):
    get_manager(prefix).update(
        request.time_scale_factor,
        request.sim_update_time
    )

@app.post("/testScript/{prefix}")
def exeute_test_plan(prefix: str, request: ExecuteRequest):
    #TODO this manager function is synchronous
    get_manager(prefix).execute_test_plan(
        request.sim_start_time,
        request.sim_stop_time,
        request.start_time,
        request.time_step,
        request.time_scale_factor,
        [u.to_manager_format() for u in request.time_scale_updates],
        request.time_status_step,
        request.time_status_init,
        request.command_lead,
        request.required_apps,
        request.init_retry_delay_s,
        request.init_max_retry
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=3000, reload=True)