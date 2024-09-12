from skyfield.api import EarthSatellite, load, utc
from datetime import datetime, timedelta
from skyfield.api import wgs84
import plotly.graph_objects as go
import json

# Load the timescale
ts = load.timescale()

# Load the TLE data for Capella
capella = EarthSatellite(
    "1 59444U 24066C   24255.58733490  .00027683  00000+0  27717-2 0  9992",
    "2 59444  45.6105 355.6094 0002469 338.3298  21.7475 14.91016875 15732",
    "CAPELLA-14 (ACADIA-4)",
    ts=ts,
)

# Define the duration for which the loop should run (e.g., 1 minute)
end_time = datetime.now().replace(tzinfo=utc) + timedelta(minutes=1)

# Initialize the figure
fig = go.Figure()

# Function to get satellite position
def get_satellite_position():
    current_time = datetime.now().replace(tzinfo=utc)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    position = capella.at(ts.from_datetime(current_time))
    lat, lon = wgs84.latlon_of(position)
    height = wgs84.height_of(position)
    return {
        "time": formatted_time,
        "lat": lat.degrees,
        "lon": lon.degrees,
        "height": height.km
    }

# Get initial position
position_data = get_satellite_position()

# Save the initial position data to a JSON file
with open("position_data.json", "w") as f:
    json.dump(position_data, f)

# Update the figure with the initial position
fig.add_trace(go.Scattergeo(
    lon=[position_data["lon"]],
    lat=[position_data["lat"]],
    text=f"Time: {position_data['time']}<br>Height: {position_data['height']:.2f} km",
    mode='markers',
    marker=dict(
        size=10,
        color='red',
        symbol='circle'
    )
))

# Update the layout of the figure
fig.update_layout(
    title='Capella Satellite Position',
    geo=dict(
        projection_type='equirectangular',
        showland=True,
        landcolor='rgb(243, 243, 243)',
        subunitwidth=1,
        countrywidth=1,
        subunitcolor='rgb(217, 217, 217)',
        countrycolor='rgb(217, 217, 217)'
    )
)

# Save the figure as an HTML file
fig.write_html("capella_satellite_position.html")
