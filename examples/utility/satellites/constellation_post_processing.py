# -*- coding: utf-8 -*-
"""
*This script contains a post-processing script for plotting times recorded by the main_constellation.py application*

Placeholder

"""
import numpy as np
import pandas as pd
from datetime import timedelta, datetime, timezone
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

from scipy import stats
# from scipy.stats import skew, kurtosis

font1 = {"family": "sans-serif", "weight": "bold", "size": 24}
font1 = {"family": "sans-serif", "weight": "bold", "size": 10}

start = pd.DataFrame(constellation.fires)
start.set_index("fireId", inplace=True)
detect = pd.DataFrame(constellation.detect)
detect.set_index("fireId", inplace=True)
report = pd.DataFrame(constellation.report)
report.set_index("fireId", inplace=True)

detect["AQUA"] = (
    reported_fires["detected"] - reported_fires["start"]
).dt.seconds
reported_fires["Time to Report [s]"] = (
    reported_fires["reported"] - reported_fires["start"]
).dt.seconds
reported_fires["Detect-Report Delay [s]"] = (
    reported_fires["reported"] - reported_fires["detected"]
).dt.seconds
reported_fires["Match?"] = (
    reported_fires["detected_by"] == reported_fires["reported_by"]
)

sns.set_style("white")
plt.figure(figsize=(12,10))
sns.displot(
    reported_fires, x="Time to Report [s]", hue="reported_by")
plt.savefig("Three_Sats_5days.svg", format="svg")

stats = {
        'mean detect (s)': np.mean(reported_fires["Time to Detect [s]"]),
        'mean report (s)': np.mean(reported_fires["Time to Report [s]"]),
        'median detect (s)': np.median(reported_fires["Time to Detect [s]"]),
        'median report (s)': np.median(reported_fires["Time to Report [s]"]),
        'mode detect (s)': stats.mstats.mode(reported_fires["Time to Detect [s]"])[0][0],
        'mode report (s)': stats.mstats.mode(reported_fires["Time to Report [s]"])[0][0],
        'standard deviation detect (s)': np.std(reported_fires["Time to Detect [s]"]),
        'standard deviation report (s)': np.std(reported_fires["Time to Report [s]"]),
        '25th percentile detect (s)': np.percentile(reported_fires["Time to Detect [s]"],25),
        '25th percentile report (s)': np.percentile(reported_fires["Time to Report [s]"],25),
        '75th percentile detect (s)': np.percentile(reported_fires["Time to Detect [s]"],75),
        '75th percentile report (s)': np.percentile(reported_fires["Time to Report [s]"],75),
    }

# aqua = reported_fires[reported_fires["reported_by"] == "AQUA (MODIS)"]
# sns.displot(aqua, x="Time to Report [s]")

# terra = reported_fires[reported_fires["reported_by"] == "TERRA (MODIS)"]
# sns.displot(terra, x="Time to Report [s]")

# npp = reported_fires[reported_fires["reported_by"] == "SUOMI NPP (VIIRS)"]
# sns.displot(npp, x="Time to Report [s]")
