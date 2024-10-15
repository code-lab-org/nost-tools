from flask import Flask, jsonify, send_from_directory
from skyfield.api import EarthSatellite, load, utc
from datetime import datetime, timezone
from skyfield.api import wgs84
from skyfield.framelib import itrs
import numpy as np
import math
from satellite_tle import fetch_all_tles, fetch_latest_tles
import matplotlib.pyplot as plt

import netCDF4 as nc
# import matplotlib.pyplot as plt
import base64
# import numpy as np
# from mpl_toolkits.axes_grid1 import make_axes_locatable

def calculate_angular_width(altitude_m):
    altitude_km = altitude_m / 1000
    R = 6371
    theta_radians = 2 * math.atan(R / (R + altitude_km))
    theta_degrees = math.degrees(theta_radians)
    return theta_degrees

def compute_min_elevation(altitude, field_of_regard):
    earth_equatorial_radius = 6378137.000000000
    earth_polar_radius = 6356752.314245179
    earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3
    sin_eta = np.sin(np.radians(field_of_regard / 2))
    sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
    cos_epsilon = sin_eta / sin_rho
    if cos_epsilon > 1:
        return 0.0
    return np.degrees(np.arccos(cos_epsilon))

def compute_sensor_radius(altitude, min_elevation):
    earth_equatorial_radius = 6378137.0
    earth_polar_radius = 6356752.314245179
    earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3
    sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
    eta = np.degrees(np.arcsin(np.cos(np.radians(min_elevation)) * sin_rho))
    sw_HalfAngle = 90 - eta - min_elevation
    if sw_HalfAngle < 0.0:
        return 0.0
    return earth_mean_radius * np.radians(sw_HalfAngle)

def get_tles(automate=True):
    if automate:
        # Define the NORAD IDs
        norad_ids = [59444,  # CAPELLA-14 (ACADIA-4)
                     38337]  # GCOM-W1 (SHIZUKU)
                    #  43013]  # NOAA 20 (JPSS-1)

        # Fetch the latest TLEs for the satellites
        tles = fetch_latest_tles(norad_ids)

        # Define the satellite objects
        satellite_objects = [EarthSatellite(tle[1][1], tle[1][2], str(tle[1][0]), ts=ts) for norad_id, tle in tles.items()]
        
        # Check if satellite_objects is empty
        if not satellite_objects:
            return use_manual_tles()
        return satellite_objects
    else:
        return use_manual_tles()

def use_manual_tles():

    # Define the satellites
    satellites = [
        {
            "name": "CAPELLA-14 (ACADIA-4)",
            "tle": [
                "1 59444U 24066C   24255.58733490  .00027683  00000+0  27717-2 0  9992",
                "2 59444  45.6105 355.6094 0002469 338.3298  21.7475 14.91016875 15732"
            ]
        },
        {
            "name": "GCOM-W1 (SHIZUKU)",
            "tle": [
                "1 38337U 12025A   24256.58148722  .00002449  00000+0  55400-3 0  9995",
                "2 38337  98.2068 195.3055 0002169 106.7341  66.3204 14.57058865655452"
            ]
        },
        # {
        #     "name": "NOAA 20 (JPSS-1)",
        #     "tle": [
        #         "1 43013U 17073A   24260.54824830  .00000349  00000+0  18598-3 0  9996",
        #         "2 43013  98.7099 196.9501 0001127  22.2184 337.9041 14.19588559353863"
        #     ]
        # }
    ]

    # Load the satellites
    satellite_objects = [
        EarthSatellite(sat["tle"][0], sat["tle"][1], sat["name"], ts=ts)
        for sat in satellites
    ]
    return satellite_objects

def get_extents(dataset, variable):
    # Extract the GeoTransform attribute
    geo_transform = dataset.variables['spatial_ref'].GeoTransform.split()
    print(geo_transform)

    # Convert GeoTransform values to float
    geo_transform = [float(value) for value in geo_transform]

    # Calculate the extents (four corners)
    min_x = geo_transform[0]
    pixel_width = geo_transform[1]
    max_y = geo_transform[3]
    pixel_height = geo_transform[5]

    # Get the actual dimensions of the raster layer
    n_rows, n_cols = dataset.variables[variable][0, :, :].shape

    # Calculate the coordinates of the four corners
    top_left = (min_x, max_y)
    top_right = (min_x + n_cols * pixel_width, max_y)
    bottom_left = (min_x, max_y + n_rows * pixel_height)
    bottom_right = (min_x + n_cols * pixel_width, max_y + n_rows * pixel_height)

    return top_left, top_right, bottom_left, bottom_right

def open_netcdf(file_path):
    # Open the NetCDF file
    dataset = nc.Dataset(file_path, mode='r')

    return dataset

def encode_raster_layer(dataset, variable):
    # Extract snow cover
    raster_layer = dataset.variables[variable][0, :, :]

    # Convert the array to bytes and encode the bytes in base64
    bytes = raster_layer.tobytes()
    base64_raster_layer = base64.b64encode(bytes).decode('utf-8')

    return raster_layer, base64_raster_layer

def decode_raster_layer(raster_layer, base64_raster_layer):
    # Decode the base64 string back to bytes
    decoded_bytes = base64.b64decode(base64_raster_layer)
    decoded_raster_layer = np.frombuffer(decoded_bytes, dtype=raster_layer.dtype).reshape(raster_layer.shape)

    return decoded_raster_layer

# def open_encode(file_path, variable, output_path):
#     # Open the NetCDF file
#     dataset = open_netcdf(file_path)

#     # Extract array
#     raster_layer = dataset.variables[variable][0, :, :]

#     # Get the extents (four corners) coordinates
#     top_left, top_right, bottom_left, bottom_right = get_extents(dataset, variable=variable)

#     # # Encode the raster layer
#     # raster_layer, base64_raster_layer = encode_raster_layer(dataset, variable=variable)

#     # # Decode the raster layer
#     # decoded_raster_layer = decode_raster_layer(raster_layer, base64_raster_layer)

#     # Save array to PNG, then encode to base64
#     plt.imsave(output_path, raster_layer, cmap='cividis')
#     raster_layer_encoded = encode_image(output_path)

#     return raster_layer_encoded, top_left, top_right, bottom_left, bottom_right #raster_layer, base64_raster_layer, top_left, top_right, bottom_left, bottom_right

def open_encode(file_path, variable, output_path):
    # Open the NetCDF file
    dataset = open_netcdf(file_path)

    # Extract array
    raster_layer = dataset.variables[variable][0, :, :]

    # Normalize the raster layer to the range [0, 1]
    raster_layer_normalized = (raster_layer - np.min(raster_layer)) / (np.max(raster_layer) - np.min(raster_layer))

    # Get the extents (four corners) coordinates
    top_left, top_right, bottom_left, bottom_right = get_extents(dataset, variable=variable)

    # Save normalized array to PNG with colormap
    plt.imsave(output_path, raster_layer_normalized, cmap='viridis')
    raster_layer_encoded = encode_image(output_path)

    return raster_layer_encoded, top_left, top_right, bottom_left, bottom_right

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

app = Flask(__name__)

# Load the timescale
ts = load.timescale()

satellite_objects = get_tles() #automate=False)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/get_positions')
def get_positions():
    current_datetime = datetime.now(timezone.utc)
    positions = []

    snow_layer, top_left, top_right, bottom_left, bottom_right = open_encode(
        # file_path='/mnt/c/Users/emgonz38/OneDrive - Arizona State University/ubuntu_files/netcdf_encode/input_data/Efficiency_resolution20_Optimization/efficiency_snow_cover.nc',
        # variable='Day_CMG_Snow_Cover',
        # output_path='snow_raster_layer_high_resolution.png'
        file_path='/mnt/c/Users/emgonz38/OneDrive - Arizona State University/ubuntu_files/netcdf_encode/input_data/Efficiency_high_resolution_Caesium/efficiency_snow_cover_highest_resolution.nc',
        variable='Weekly_Snow_Cover',
        output_path='snow_raster_layer_high_resolution.png'
        )

    resolution_layer, top_left, top_right, bottom_left, bottom_right = open_encode(
        # file_path='/mnt/c/Users/emgonz38/OneDrive - Arizona State University/ubuntu_files/netcdf_encode/input_data/Efficiency_resolution20_Optimization/efficiency_resolution_layer.nc',
        # variable='Monthly_Resolution_Abs',
        # output_path='resolution_raster_layer_high_resolution.png'
        file_path='/mnt/c/Users/emgonz38/OneDrive - Arizona State University/ubuntu_files/netcdf_encode/input_data/Efficiency_high_resolution_Caesium/efficiency_resolution_layer_highest_resolution.nc',
        variable='Monthly_Resolution_Abs',
        output_path='resolution_raster_layer_high_resolution.png'
        )

    for satellite in satellite_objects:

        # Get the geographic position of the satellite
        position = satellite.at(ts.from_datetime(current_datetime))
        subpoint = wgs84.subpoint(position)
        lat, lon = subpoint.latitude, subpoint.longitude
        altitude_meters = subpoint.elevation.m

        # Get the cartesian posotion of the satellite
        x, y, z = position.frame_xyz(itrs).m
        ecef_position = position.position.m
        ecef_x, ecef_y, ecef_z = ecef_position

        # Get the velocity of the satellite
        velocity = position.velocity.km_per_s
        velocity_x, velocity_y, velocity_z = velocity
        
        #Get the angular width of the satellite
        min_elevation = 0
        sensor_radius_meters = compute_sensor_radius(altitude_meters, min_elevation)
        print(top_left, top_right, bottom_left, bottom_right)
        # Add the satellite to the list of positions
        positions.append({
            'name': satellite.name,
            'latitude': lat.degrees,
            'longitude': lon.degrees,
            'altitude': altitude_meters,
            'radius': sensor_radius_meters,
            'velocity': [velocity_x, velocity_y, velocity_z],
            'state': True,
            'time': current_datetime,
            'ecef': [x, y, z],
            'snow_layer': snow_layer,
            'resolution_layer': resolution_layer,
            'top_left': top_left,
            'top_right': top_right,
            'bottom_left': bottom_left,
            'bottom_right': bottom_right
        })

    return jsonify(positions)

@app.route('/env.js')
def env_js():
    return send_from_directory('.', 'env.js')

@app.route('/resolution_raster_layer_high_resolution.png')
def get_resolution_raster_layer():
    return send_from_directory(directory='.', path='resolution_raster_layer_high_resolution.png')

@app.route('/snow_raster_layer_high_resolution.png')
def get_snow_raster_layer():
    return send_from_directory(directory='.', path='snow_raster_layer_high_resolution.png')

if __name__ == '__main__':
    app.run(debug=True, port=7000) #8080)