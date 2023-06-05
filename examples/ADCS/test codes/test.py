# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 11:25:51 2023

@author: brian
"""

from scipy.spatial.transform import Rotation as R
import numpy as np

from skyfield.api import load, wgs84, EarthSatellite
from nost_tools.entity import Entity
from nost_tools.publisher import WallclockTimeIntervalPublisher

from schemas import *

from datetime import datetime

pos = [-2816582.1169761578,5558754.36738815,-3627165.10070542]
vel = [2816.061592708052,-2696.949835438608,-6328.40399288645]

posMag = np.linalg.norm(pos)
velMag = np.linalg.norm(vel)
att = vel/velMag                      # normalized velocity = attitude in geo coordinates?

b_x = vel/velMag                      # body x-axis along velocity vector
b_z = pos/posMag                      # body z-axis nadir pointing
b_y = np.cross(b_x,b_z)               # body y-axis normal to orbital plane

dcm_0 = np.stack([b_x, b_y, b_z])     # initial dcm from inertial to body coordinates

r = R.from_matrix(dcm_0)

quat_0 = r.as_quat()                  # initial quaternion from inertial to body coordinates

newAtt = r.apply(att)


