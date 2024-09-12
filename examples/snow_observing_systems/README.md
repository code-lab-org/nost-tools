# Snow Observing Systems Visualization

## Overview
This project visualizes the position and sensor radius of the CAPELLA-14 (ACADIA-4) satellite in real-time using Flask for the backend and CesiumJS for the frontend.

## Project Structure

- **index.html**: The frontend of the application, which uses CesiumJS to visualize the satellite's position.
- **server.py**: The backend of the application, which uses Flask to serve endpoints and Skyfield to compute satellite positions.
- **env.js**: Contains environment variables such as the API token.
- **requirements.txt**: Lists the Python dependencies required to run the project.

## Cesium Access Token and Assets
The SOS application uses the Cesium geospatial visualization tool which requires getting an access token and an 3D Earth map asset. You will get an access token by signing in at the following link:

https://cesium.com/ion/signin/tokens

After creating an account, you must add the Asset “Blue Marble Next Generation July, 2004” from the Asset Depot (ID 3845) to your account assets to enable visualization.

## Setting Up Environment Files

You must create the **env.js** file at ```nost-tools/examples/snow_observing_systems```, which contains the Cesium API token in the following format:

```
var TOKEN="your_cesium_api_token"
```

## Installation
1. Clone the repository:
    ```sh
    git clone git@github.com:emmanuelgonz/nost-tools.git
    cd nost-tools/examples/snow_observing_systems
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

## Running the Project
1. Start the Flask server:
    ```sh
    python server.py
    ```

2. Open `index.html` in a web browser to view the visualization.

## Endpoints
- **/**: Serves the main page.
- **/get_position**: Returns the current position and sensor radius of the satellite in JSON format.
- **/env.js**: Serves the environment variables.

## Example Output
```json
{
    "name": "CAPELLA-14 (ACADIA-4)",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude": 500.0,
    "radius": 1000.0,
    "velocity": [7.5, 0.0, 0.0],
    "state": true,
    "time": "2023-10-01T12:00:00Z"
}
```