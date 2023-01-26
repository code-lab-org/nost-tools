# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 18:44:48 2023

@author: brian
"""

from scipy.spatial.transform import Rotation as R
import numpy as np

#rot matrix for 45 degree y axis



# zero rot
# zero_rot = [[1, 0, 0],
#             [0, 1, 0],
#             [0, 0, 1]]
# zero_quat = ([0., 0., 0., 1.])
# dcm_0_nominal = np.array(zero_rot)
# zero rot

dcm_nom = np.array([[ 0.707107, -0, -0.707107],
              [0, 1, -0],
              [0.707107, 0, 0.707107]])

# 45 deg about y
q0 = np.array([0, 0.382683, 0, 0.92388])


q_maneuver = [0, 0.707107, 0, 0.707107]


r = R.from_quat(q0)

r.as_rotvec()

q_actual = np.load("mgd_q_actual.npy")

results = []
i = 0
    
for i in range(len(q_actual)):
    
    r = R.from_quat(q_actual[i])
    x=r.as_rotvec(degrees=True)
    results.append(x)
    
xyz=np.array(results)

