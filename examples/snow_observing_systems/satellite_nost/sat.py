from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
from skyfield.api import load, wgs84, EarthSatellite
from skyfield.framelib import itrs
import numpy as np
import logging
import pandas as pd

import netCDF4 as nc
import base64
import matplotlib.pyplot as plt
from PIL import Image
import io
import xarray as xr
import geopandas as gpd
import rioxarray

from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.entity import Entity
from nost_tools.managed_application import ManagedApplication
from nost_tools.publisher import WallclockTimeIntervalPublisher

from constellation_config_files.schemas import SatelliteStatus, SnowLayer, ResolutionLayer, GcomLayer, CapellaLayer
from constellation_config_files.config import PREFIX, NAME, SCALE, TLES, FIELD_OF_REGARD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def get_elevation_angle(t, sat, loc):
    """
    Returns the elevation angle (degrees) of satellite with respect to the topocentric horizon.

    Args:
        t (:obj:`Time`): Time object of skyfield.timelib module
        sat (:obj:`EarthSatellite`): Skyview EarthSatellite object from skyfield.sgp4lib module
        loc (:obj:`GeographicPosition`): Geographic location on surface specified by latitude-longitude from skyfield.toposlib module

    Returns:
        float : alt.degrees
            Elevation angle (degrees) of satellite with respect to the topocentric horizon
    """
    difference = sat - loc
    topocentric = difference.at(t)
    # NOTE: Topos uses term altitude for what we are referring to as elevation
    alt, az, distance = topocentric.altaz()
    return alt.degrees

def compute_sensor_radius(altitude, min_elevation):
    """
    Computes the sensor radius for a satellite at current altitude given minimum elevation constraints.

    Args:
        altitude (float): Altitude (meters) above surface of the observation
        min_elevation (float): Minimum angle (degrees) with horizon for visibility

    Returns:
        float : sensor_radius
            The radius (meters) of the nadir pointing sensors circular view of observation
    """
    earth_equatorial_radius = 6378137.0
    earth_polar_radius = 6356752.314245179
    earth_mean_radius = (2 * earth_equatorial_radius + earth_polar_radius) / 3
    # rho is the angular radius of the earth viewed by the satellite
    sin_rho = earth_mean_radius / (earth_mean_radius + altitude)
    # eta is the nadir angle between the sub-satellite direction and the target location on the surface
    eta = np.degrees(np.arcsin(np.cos(np.radians(min_elevation)) * sin_rho))
    # calculate swath width half angle from trigonometry
    sw_HalfAngle = 90 - eta - min_elevation
    if sw_HalfAngle < 0.0:
        return 0.0
    return earth_mean_radius * np.radians(sw_HalfAngle)

class Constellation(Entity):
    ts = load.timescale()
    PROPERTY_POSITION = "position"

    def __init__(self, cName, app, id, names, ES=None, tles=None):
        super().__init__(cName)
        self.app = app
        self.id = id
        self.names = names
        self.satellites = []
        if ES is not None:
            for satellite in ES:
                self.satellites.append(satellite)
        if tles is not None:
            for i, tle in enumerate(tles):
                self.satellites.append(
                    EarthSatellite(tle[0], tle[1], self.names[i], self.ts)
                )
        self.positions = self.next_positions = [None for satellite in self.satellites]

    def initialize(self, init_time):
        super().initialize(init_time)
        self.positions = self.next_positions = [
            wgs84.subpoint(satellite.at(self.ts.from_datetime(init_time)))
            for satellite in self.satellites
        ]
        
# define a publisher to report satellite status
class PositionPublisher(WallclockTimeIntervalPublisher):
    """
    *This object class inherits properties from the WallclockTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

    The user can optionally specify the wallclock :obj:`timedelta` between message publications and the scenario :obj:`datetime` when the first of these messages should be published.

    Args:
        app (:obj:`ManagedApplication`): An application containing a test-run namespace, a name and description for the app, client credentials, and simulation timing instructions
        constellation (:obj:`Constellation`): Constellation :obj:`Entity` object class
        time_status_step (:obj:`timedelta`): Optional duration between time status 'heartbeat' messages
        time_status_init (:obj:`datetime`): Optional scenario :obj:`datetime` for publishing the first time status 'heartbeat' message

    """

    def __init__(
        self, app, constellation, time_status_step=None, time_status_init=None,
        snow_layer=None, resolution_layer=None, gcom_layer=None, capella_layer=None,
        top_left=None, top_right=None, bottom_left=None, bottom_right=None
    ):
        super().__init__(app, time_status_step, time_status_init)
        self.constellation = constellation
        self.snow_layer = snow_layer
        self.resolution_layer = resolution_layer
        self.gcom_layer = gcom_layer
        self.capella_layer = capella_layer
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right

        if self.time_status_init is None:
            self.time_status_init = self.constellation.ts.now().utc_datetime()
    
    def get_extents(self, dataset, variable):
        # Extract the GeoTransform attribute
        geo_transform = dataset['spatial_ref'].GeoTransform.split()
        # Convert GeoTransform values to float
        geo_transform = [float(value) for value in geo_transform]
        # Calculate the extents (four corners)
        min_x = geo_transform[0]
        pixel_width = geo_transform[1]
        max_y = geo_transform[3]
        pixel_height = geo_transform[5]
        # Get the actual dimensions of the raster layer
        n_rows, n_cols = dataset[variable][0, :, :].shape
        # Calculate the coordinates of the four corners
        top_left = (min_x, max_y)
        top_right = (min_x + n_cols * pixel_width, max_y)
        bottom_left = (min_x, max_y + n_rows * pixel_height)
        bottom_right = (min_x + n_cols * pixel_width, max_y + n_rows * pixel_height)
        return top_left, top_right, bottom_left, bottom_right

    def open_netcdf(self, file_path, time_step):
        # Open the NetCDF file
        # dataset = nc.Dataset(file_path, mode='r')
        dataset = xr.open_dataset(file_path)
        # dataset = dataset.time.isel(time=time_step)

        return dataset

    def downsample_array(self, array, factor):
        """
        Downsamples the given array by the specified factor.

        Args:
            array (np.ndarray): The array to downsample.
            factor (int): The factor by which to downsample the array.

        Returns:
            np.ndarray: The downsampled array.
        """
        return array[::factor, ::factor]
    
    def open_encode(self, file_path, variable, output_path, time_step, scale, geojson_path, downsample_factor=1):
        # Load the GeoJSON file to get the polygon geometry
        geojson = gpd.read_file(geojson_path)
        polygons = geojson.geometry
    
        # Open the NetCDF file
        dataset = self.open_netcdf(file_path, time_step)
        raster_layer = dataset[variable]
    
        # Clip the raster layer to the polygon geometry
        raster_layer = raster_layer.rio.write_crs("EPSG:4326")  # Ensure the CRS is set
        clipped_layer = raster_layer.rio.clip(polygons, all_touched=True)
    
        # Extract array
        if scale == 'time':
            raster_layer = clipped_layer.isel(time=time_step).values
        elif scale == 'week':
            raster_layer = clipped_layer.isel(week=time_step).values
        elif scale == 'month':
            raster_layer = clipped_layer.isel(month=time_step).values
        
        # Downsample the array
        raster_layer = self.downsample_array(raster_layer, downsample_factor)

        # Normalize the array to the range [0, 1]
        raster_layer_min = np.nanmin(raster_layer)
        raster_layer_max = np.nanmax(raster_layer)
    
        # Create a mask for NA values
        na_mask = np.isnan(raster_layer)
    
        if raster_layer_max > raster_layer_min:  # Avoid division by zero
            normalized_layer = (raster_layer - raster_layer_min) / (raster_layer_max - raster_layer_min)
        else:
            normalized_layer = np.zeros_like(raster_layer)  # If all values are the same, set to zero
    
        # Apply the Blues colormap
        colormap = plt.get_cmap('Blues_r')
        rgba_image = colormap(normalized_layer)
    
        # Set the alpha channel: 0 for NA, 1 for others
        rgba_image[..., 3] = np.where(na_mask, 0, 1)
    
        # Convert to 8-bit unsigned integer
        rgba_image = (rgba_image * 255).astype(np.uint8)
    
        # Save the RGBA image
        image = Image.fromarray(rgba_image, 'RGBA')
        image.save(output_path)
    
        # Get the extents (four corners) coordinates
        top_left, top_right, bottom_left, bottom_right = self.get_extents(dataset, variable=variable)
    
        # Save the image to a BytesIO object
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
    
        # Encode image to base64
        raster_layer_encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
        return raster_layer_encoded, top_left, top_right, bottom_left, bottom_right

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def publish_message(self):
        """
        *Abstract publish_message method inherited from the WallclockTimeIntervalPublisher object class from the publisher template in the NOS-T tools library*

        This method sends a :obj:`SatelliteStatus` message to the *PREFIX/constellation/location* topic for each satellite in the constellation (:obj:`Constellation`).

        """
        current_time = constellation.get_time()
        elapsed_seconds = (current_time - self.time_status_init).total_seconds()
        current_minute = (elapsed_seconds // 60) % 100
        
        swath_data = {
            'CAPELLA-14 (ACADIA-4)': 5000, #30000, # Swath value in m 
            'GCOM-W1 (SHIZUKU)': 1450000 # Swath value in m
            }
        
        for i, satellite in enumerate(self.constellation.satellites):
            next_time = constellation.ts.from_datetime(
                constellation.get_time() + 60 * self.time_status_step
            )
            
            # Get the subpoint of the satellite
            satSpaceTime = satellite.at(next_time)

            # Determine if the satellite is operational
            if satellite.name=='CAPELLA-14 (ACADIA-4)':
                state = current_minute < 5
            elif satellite.name=='GCOM-W1 (SHIZUKU)':
                state = True

            # Get the cartesian position of the satellite in International Terrestrial Reference System (ITRS)
            position, velocity = satSpaceTime.frame_xyz_and_velocity(itrs)
            # Origin of the coordinate system is at the center of mass of the Earth, and the axes are fixed relative to the Earth
            x, y, z = position.m
            velocity_x, velocity_y, velocity_z = velocity.km_per_s

            # Get the geographic position of the satellite
            lat, lon = wgs84.latlon_of(satSpaceTime)
            altitude = wgs84.height_of(satSpaceTime)

            #Get the angular width of the satellite
            sensorRadius = compute_sensor_radius(
                altitude.m, # subpoint.elevation.m, 
                0
            )

            self.app.send_message(
                self.app.app_name,
                "location",
                SatelliteStatus(
                    id=i,
                    name=satellite.name,
                    latitude=lat.degrees,
                    longitude=lon.degrees,
                    altitude=altitude.m,
                    radius=sensorRadius,
                    velocity=[velocity_x, velocity_y, velocity_z],
                    state=state,
                    swath=swath_data.get(satellite.name, 0),
                    time=constellation.get_time(),
                    ecef=[x, y, z],
                    # snow_layer=self.snow_layer,
                    # resolution_layer=self.resolution_layer,
                    # gcom_layer=self.gcom_layer,
                    # capella_layer=self.capella_layer,
                    # top_left=self.top_left,
                    # top_right=self.top_right,
                    # bottom_left=self.bottom_left,
                    # bottom_right=self.bottom_right
                ).json(),
            )

# Function to read and encode the layers
def read_and_encode_layers(position_publisher):
    snow_layer, top_left, top_right, bottom_left, bottom_right = position_publisher.open_encode(
        file_path='../input_data/Efficiency_high_resolution_Caesium/efficiency_snow_cover_highest_resolution.nc',
        variable='Weekly_Snow_Cover',
        output_path='snow_raster_layer.png',
        scale='week',
        time_step=3,
        geojson_path='../WBD_10_HU2_4326.geojson'
    )

    resolution_layer, top_left, top_right, bottom_left, bottom_right = position_publisher.open_encode(
        file_path='../input_data/Efficiency_high_resolution_Caesium/efficiency_resolution_layer_highest_resolution.nc',
        variable='Monthly_Resolution_Abs',
        output_path='resolution_raster_layer.png',
        scale='month',
        time_step=0,
        geojson_path='../WBD_10_HU2_4326.geojson'
    )

    gcom_layer, top_left, top_right, bottom_left, bottom_right = position_publisher.open_encode(
        file_path='../input_data/Optimization/final_eta_combined_output_GCOM.nc',
        variable='final_eta_result',
        output_path='gcom_optimization.png',
        scale='time',
        time_step=1,
        geojson_path='../WBD_10_HU2_4326.geojson'
    )

    capella_layer, top_left, top_right, bottom_left, bottom_right = position_publisher.open_encode(
        file_path='../input_data/Optimization/final_eta_combined_output_Capella.nc',
        variable='final_eta_result',
        output_path='capella_optimization.png',
        scale='time',
        time_step=1,
        geojson_path='../WBD_10_HU2_4326.geojson'
    )

    return snow_layer, resolution_layer, gcom_layer, capella_layer, top_left, top_right, bottom_left, bottom_right

# Main function
if __name__ == "__main__":
    credentials = dotenv_values(".env")
    HOST, RABBITMQ_PORT, KEYCLOAK_PORT, KEYCLOAK_REALM = credentials["HOST"], int(credentials["RABBITMQ_PORT"]), int(credentials["KEYCLOAK_PORT"]), str(credentials["KEYCLOAK_REALM"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]
    CLIENT_ID = credentials["CLIENT_ID"]
    CLIENT_SECRET_KEY = credentials["CLIENT_SECRET_KEY"]
    VIRTUAL_HOST = credentials["VIRTUAL_HOST"]
    IS_TLS = credentials["IS_TLS"].lower() == 'true'

    config = ConnectionConfig(
        USERNAME,
        PASSWORD,
        HOST,
        RABBITMQ_PORT,
        KEYCLOAK_PORT,
        KEYCLOAK_REALM,
        CLIENT_ID,
        CLIENT_SECRET_KEY,
        VIRTUAL_HOST,
        IS_TLS)

    app = ManagedApplication(NAME)

    activesats_url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    activesats = load.tle_file(activesats_url, reload=False, filename='./active.txt') #True

    by_name = {sat.name: sat for sat in activesats}
    names = ['CAPELLA-14 (ACADIA-4)', 'GCOM-W1 (SHIZUKU)']
            #  "AQUA", "TERRA", "SUOMI NPP", "NOAA 20 (JPSS-1)", "SENTINEL-2A", "SENTINEL-2B"] #'CAPELLA-14 (ACADIA)'

    ES = []
    indices = []
    for name_i, name in enumerate(names):
        name = str(name).strip()
        if name in by_name:
            ES.append(by_name[name])
            indices.append(name_i)
        else:
            logger.warning(f"Key '{name}' does not exist in the 'by_name' dictionary.")

    constellation = Constellation("constellation", app, indices, names, ES)
    app.simulator.add_entity(constellation)
    app.simulator.add_observer(ShutDownObserver(app))

    # Initialize PositionPublisher and read layers
    position_publisher = PositionPublisher(app, constellation, timedelta(seconds=1))
    snow_layer, resolution_layer, gcom_layer, capella_layer, top_left, top_right, bottom_left, bottom_right = read_and_encode_layers(position_publisher)
    
    # Pass the layers to the PositionPublisher
    position_publisher.snow_layer = snow_layer
    position_publisher.resolution_layer = resolution_layer
    position_publisher.gcom_layer = gcom_layer
    position_publisher.capella_layer = capella_layer
    position_publisher.top_left = top_left
    position_publisher.top_right = top_right
    position_publisher.bottom_left = bottom_left
    position_publisher.bottom_right = bottom_right

    app.simulator.add_observer(position_publisher)

    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime.now(timezone.utc),
        time_step=timedelta(seconds=1) * SCALE,
    )

    # while True:
    #     pass