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

class LayerPublisher(WallclockTimeIntervalPublisher):
    def __init__(
            self, app, time_status_step = None, time_status_init = None,
            snow_layer=None, resolution_layer=None, gcom_layer=None, capella_layer=None,
            top_left=None, top_right=None, bottom_left=None, bottom_right=None):
        super().__init__(app, time_status_step, time_status_init)
        self.snow_layer = snow_layer
        self.resolution_layer = resolution_layer
        self.gcom_layer = gcom_layer
        self.capella_layer = capella_layer
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right

        # if self.time_status_init is None:
        #     self.time_status_init = self.constellation.ts.now().utc_datetime()
    
    def publish_message(self):

        self.app.send_message(
            self.app.app_name,
            "snow_layer",
            SnowLayer(
                snow_layer=self.snow_layer,
                top_left=self.top_left,
                top_right=self.top_right,
                bottom_left=self.bottom_left,
                bottom_right=self.bottom_right
            ).json(),
        )

        self.app.send_message(
            self.app.app_name,
            "resolution_layer",
            ResolutionLayer(
                resolution_layer=self.resolution_layer,
                top_left=self.top_left,
                top_right=self.top_right,
                bottom_left=self.bottom_left,
                bottom_right=self.bottom_right
            ).json(),
        )

        self.app.send_message(
            self.app.app_name,
            "gcom_layer",
            GcomLayer(
                gcom_layer=self.gcom_layer,
                top_left=self.top_left,
                top_right=self.top_right,
                bottom_left=self.bottom_left,
                bottom_right=self.bottom_right
            ).json(),
        )

        self.app.send_message(
            self.app.app_name,
            "capella_layer",
            CapellaLayer(
                capella_layer=self.capella_layer,
                top_left=self.top_left,
                top_right=self.top_right,
                bottom_left=self.bottom_left,
                bottom_right=self.bottom_right
            ).json(),
        )

def get_extents(dataset, variable):
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

def open_netcdf(file_path, time_step):
    # Open the NetCDF file
    # dataset = nc.Dataset(file_path, mode='r')
    dataset = xr.open_dataset(file_path)
    # dataset = dataset.time.isel(time=time_step)

    return dataset

def downsample_array(array, factor):
    """
    Downsamples the given array by the specified factor.

    Args:
        array (np.ndarray): The array to downsample.
        factor (int): The factor by which to downsample the array.

    Returns:
        np.ndarray: The downsampled array.
    """
    return array[::factor, ::factor]

def open_encode(file_path, variable, output_path, time_step, scale, geojson_path, downsample_factor=1):
    # Load the GeoJSON file to get the polygon geometry
    geojson = gpd.read_file(geojson_path)
    polygons = geojson.geometry

    # Open the NetCDF file
    dataset = open_netcdf(file_path, time_step)
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
    raster_layer = downsample_array(raster_layer, downsample_factor)

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
    top_left, top_right, bottom_left, bottom_right = get_extents(dataset, variable=variable)

    # Save the image to a BytesIO object
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")

    # Encode image to base64
    raster_layer_encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return raster_layer_encoded, top_left, top_right, bottom_left, bottom_right

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to read and encode the layers
def read_and_encode_layers():
    snow_layer, top_left, top_right, bottom_left, bottom_right = open_encode(
        file_path='../input_data/Efficiency_high_resolution_Caesium/efficiency_snow_cover_highest_resolution.nc',
        variable='Weekly_Snow_Cover',
        output_path='snow_raster_layer.png',
        scale='week',
        time_step=3,
        geojson_path='../WBD_10_HU2_4326.geojson'
    )

    resolution_layer, top_left, top_right, bottom_left, bottom_right = open_encode(
        file_path='../input_data/Efficiency_high_resolution_Caesium/efficiency_resolution_layer_highest_resolution.nc',
        variable='Monthly_Resolution_Abs',
        output_path='resolution_raster_layer.png',
        scale='month',
        time_step=0,
        geojson_path='../WBD_10_HU2_4326.geojson'
    )

    gcom_layer, top_left, top_right, bottom_left, bottom_right = open_encode(
        file_path='../input_data/Optimization/final_eta_combined_output_GCOM.nc',
        variable='final_eta_result',
        output_path='gcom_optimization.png',
        scale='time',
        time_step=1,
        geojson_path='../WBD_10_HU2_4326.geojson'
    )

    capella_layer, top_left, top_right, bottom_left, bottom_right = open_encode(
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
    app.simulator.add_observer(ShutDownObserver(app))

    # Initialize LayerPublisher
    layer_publisher = LayerPublisher(app, timedelta(seconds=10))
    snow_layer, resolution_layer, gcom_layer, capella_layer, top_left, top_right, bottom_left, bottom_right = read_and_encode_layers()

    # Pass the layers to the PositionPublisher
    layer_publisher.snow_layer = snow_layer
    layer_publisher.resolution_layer = resolution_layer
    layer_publisher.gcom_layer = gcom_layer
    layer_publisher.capella_layer = capella_layer
    layer_publisher.top_left = top_left
    layer_publisher.top_right = top_right
    layer_publisher.bottom_left = bottom_left
    layer_publisher.bottom_right = bottom_right

    app.simulator.add_observer(layer_publisher)

    app.start_up(
        PREFIX,
        config,
        True,
        time_status_step=timedelta(seconds=10) * SCALE,
        time_status_init=datetime.now(timezone.utc),
        time_step=timedelta(seconds=1) * SCALE,
    )