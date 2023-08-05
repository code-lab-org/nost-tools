import logging
import os
from typing import Union

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import nost_tools
from nost_tools.manager import Manager
from nost_tools.application_utils import ConnectionConfig

from schemas import InitRequest, StartRequest, StopRequest, UpdateRequest, ExecuteRequest

# configure logging
logging.basicConfig(level=logging.INFO)

# create application
app = FastAPI(
    title="NOS-T Manager API",
    description="Provides a RESTful HTTP interface to NOS-T manager functions.",
    version=nost_tools.__version__
)

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

@app.get("/status/{prefix}", tags=["manager"], response_class=PlainTextResponse)
def get_scenario_mode(prefix: str):
    """
    Reports the current scenario execution mode for a prefix.
    """
    return get_manager(prefix).simulator.get_mode()

@app.post("/init/{prefix}", tags=["manager"])
def run_init_command(prefix: str, request: InitRequest):
    """
    Issues the init command to initialize a new scenario execution.
    """
    try:
        get_manager(prefix).init(
            request.sim_start_time,
            request.sim_stop_time,
            request.required_apps
        )
    except RuntimeError as err:
        raise HTTPException(status_code=400, detail=str(err))

@app.post("/start/{prefix}", tags=["manager"])
def run_start_command(prefix: str, request: StartRequest):
    """
    Issues the start command to start a new scenario execution.
    """
    try:
        get_manager(prefix).start(
            request.sim_start_time,
            request.sim_stop_time,
            request.start_time,
            request.time_step,
            request.time_scale_factor,
            request.time_status_step,
            request.time_status_init
        )
    except RuntimeError as err:
        raise HTTPException(status_code=400, detail=str(err))

@app.post("/stop/{prefix}", tags=["manager"])
def run_stop_command(prefix: str, request: StopRequest):
    """
    Issues the stop command to stop a scenario execution.
    """
    try:
        get_manager(prefix).stop(
            request.sim_stop_time
        )
    except RuntimeError as err:
        raise HTTPException(status_code=400, detail=str(err))

@app.post("/update/{prefix}", tags=["manager"])
def run_update_command(prefix: str, request: UpdateRequest):
    """
    Issues the update command to change the time scale factor of a scenario execution.
    """
    try:
        get_manager(prefix).update(
            request.time_scale_factor,
            request.sim_update_time
        )
    except RuntimeError as err:
        raise HTTPException(status_code=400, detail=str(err))

@app.post("/testScript/{prefix}", tags=["manager"])
def execute_text_plan(prefix: str, request: ExecuteRequest):
    """
    Executes a test plan to manage the end-to-end scenario execution.
    """
    #TODO this manager function is synchronous
    try:
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
    except RuntimeError as err:
        raise HTTPException(status_code=400, detail=str(err))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=3000, reload=True)