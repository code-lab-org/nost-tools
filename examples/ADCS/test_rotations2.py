# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 18:10:44 2023

@author: brian
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from skyfield.api import load, Topos, EarthSatellite, wgs84
from datetime import datetime, timezone, timedelta



# Define the position and velocity vectors
r = np.array([
 1657147.827743771,
        -645753.4810645361,
        -6989832.554930149
    ])
v = np.array([
        3666.3575964085253,
        -6291.098872505956,
        1449.9653603832396
    ])

# Calculate the specific angular momentum vector
h = np.cross(r, v)

# Calculate the unit vectors for the body x, y, and z axes

b_y = h / np.linalg.norm(h)
b_z = r / np.linalg.norm(r)
b_x0 = np.cross(b_y,b_z)
b_x = b_x0 / np.linalg.norm(b_x0)

# Calculate the rotation matrix from the body to the inertial frame
R_bo = np.vstack((b_x, b_y, b_z)).T

# Calculate the rotation matrix from the inertial to the body frame
# R_ib = R_bo.T

# Convert the rotation matrix to a quaternion
quat = R.from_matrix(R_bo).as_quat()


print("Quaternion for Cesium", quat[0], ",", quat[1], ",", quat[2], ",", quat[3])

