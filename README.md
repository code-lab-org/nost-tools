# New Observing Strategies Testbed (NOS-T)

The New Observing Strategies Testbed (NOS-T) is a computational testbed for
maturing technologies related to the NASA New Observing Strategies thrust.

Documentation: https://nost-tools.readthedocs.io

## NOS-T Tools Installation

NOS-T tools is a collection of tools for the New Observing Strategies Testbed
(NOS-T). Installing `nost-tools` as an editable Python library requires `pip`
version 23 or greater (install via `python -m pip install --upgrade pip`).

To install `nost-tools`, run the following command from the project root 
directory:

```
pip install -e .
```

Alternatively, to install supplemental libraries required for examples, run

```
pip install -e .[examples]
```

## NOS-T Tools Monitor

The NOS-T Tools Monitor application displays real-time log messages and provides access to manager commands from a browser-based interface. It consists of two components: a frontend (browser-based application) abd backend (manager API).

### Frontend



### Backend

The backend application runs a FastAPI application. To install requirements, run from the project root:
```
pip install -r monitor/requirements.txt
```
To run the backend application, run from the project root:
```
uvicorn monitor.backend.main:app --host 0.0.0.0 --port 3000
```
Swagger documentation is available at http://localhost:3000/docs

The backend application can also be run through Docker containers. To build the backend application container, run from the project root:
```
docker build -t monitor_backend --target monitor_backend .
```

To run the backend application container, run from the project root:
```
docker run -it -p 3000:3000 monitor_backend
```
Swagger documentation is available at http://localhost:3000/docs

## Contact

Principal Investigator: Paul T. Grogan <pgrogan@stevens.edu>

## Acknowledgements

This material is based on work supported, in whole or in part, by the U.S.
Department of Defense and National Aeronautics and Space Administration Earth
Science Technology Office (NASA ESTO) through the Systems Engineering Research
Center (SERC) under Contract No. W15QKN-18-D-0040. SERC is a federally funded
University Affiliated Research Center managed by Stevens Institute of
Technology. Any opinions, findings, and conclusions or recommendations
expressed in this material are those of the authors and do not necessarily
reflect the views of the United States Department of Defense.

Current project team:
 * PI: Paul T. Grogan <pgrogan@stevens.edu>
 * Brian Chell
 * Matthew LeVine
 * Leigha Capra
 * Theodore Sherman
 * Alex Yucra Castaneda

Project alumni:
 * Hayden Daly
 * Matthew Brand
 * Jerry Sellers
