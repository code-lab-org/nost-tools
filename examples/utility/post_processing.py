import pandas as pd
import numpy as np
from skyfield.api import load, wgs84
from skyfield.framelib import itrs
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

df = pd.read_csv("examples/utility/events.csv", header=2)


theta, phi = np.linspace(0, 2 * np.pi, 13), np.linspace(0, np.pi, 7)
THETA, PHI = np.meshgrid(theta, phi)
R = 6378
X = R * np.sin(PHI) * np.cos(THETA)
Y = R * np.sin(PHI) * np.sin(THETA)
Z = R * np.cos(PHI)

fig = plt.figure()
ax = plt.axes(projection='3d')



xpos = []
ypos = []
zpos = []
# Undetected events
for i, row in df.iterrows():
    if row["detected"]=="[]":
        x, y, z = wgs84.latlon(row["latitude"], row["longitude"]).itrs_xyz.km
        xpos.append(x)
        ypos.append(y)
        zpos.append(z)



ax.scatter3D(xpos, ypos, zpos, color='red')

ax.plot_wireframe(X, Y, Z, rstride=1, cstride=1, color='black')
plt.show()
