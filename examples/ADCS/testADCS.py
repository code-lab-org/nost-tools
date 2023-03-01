# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 11:25:51 2023

@author: brian
"""

from scipy.spatial.transform import Rotation as R
import numpy as np

pos = ([-2816582.1169761578,5558754.36738815,-3627165.10070542])
vel = [2816.061592708052,-2696.949835438608,-6328.40399288645]
body_0 = [0, 0, 0]

posMag = np.linalg.norm(pos)
velMag = np.linalg.norm(vel)

b_x = vel/velMag                             # body x-axis along velocity vector
b_z = pos/posMag                             # body z-axis nadir pointing
b_y = np.cross(b_x,b_z)                      # body y-axis normal to orbital plane

dcm_0 = np.stack([b_x, b_y, b_z])            # initial dcm from inertial to body coordinates

r = R.from_matrix(dcm_0)

quat_0 = r.as_quat()                          # initial quaternion from inertial to body coordinates

r2 = R.from_euler('x', 10, degrees=True)      # 10 degree roll 
quat_2 = r2.as_quat()                         # 10 degree roll quaternion
euler = r2.as_euler('xyz',degrees=True)       # check

rr = quat_2 * quat_0


att_1 = r2.apply(dcm_0)                       # updated attitude inertial coordinates?
body_1 = body_0+euler


x0, y0, z0, w0 = quat_2
x1, y1, z1, w1 = quat_0
rrr = np.array([-x1 * x0 - y1 * y0 - z1 * z0 + w1 * w0,
                 x1 * w0 + y1 * z0 - z1 * y0 + w1 * x0,
                 -x1 * z0 + y1 * w0 + z1 * x0 + w1 * y0,
                 x1 * y0 - y1 * x0 + z1 * w0 + w1 * z0], dtype=np.float64)
print(rrr)
    


p = R.from_quat([[0, 0, 1, 1], [1, 0, 0, 1]])
q = R.from_rotvec([[np.pi/4, 0, 0], [-np.pi/4, 0, np.pi/4]])
p.as_quat()
q.as_quat()
r = p * q
x = r.as_quat()



