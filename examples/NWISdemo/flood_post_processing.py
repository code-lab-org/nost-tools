# -*- coding: utf-8 -*-
"""
Created on Thu Mar  3 17:48:35 2022

@author: brian chell
"""
# -*- coding: utf-8 -*-
"""
*This script contains a post-processing script for *

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

columnNames = ["floodId", "siteName", "startTime","imageTime", "downlinkTime", "latency", "imagedBy",  "downlinkedBy"]

# for i in df.iterrows:
#     startTime = datetime.strptime(floodList[i]["startTime"],"%Y-%m-%d %H:%M:%S.%f")
# downlinkTime = datetime.strptime(y,"%Y-%m-%dT%H:%M:%S.%f")
# df = pd.DataFrame(floodList)
# df.to_csv("testData.csv")






# stats = {
#         'mean detect (s)': np.mean(reported_fires["Time to Detect [s]"]),
#         'mean report (s)': np.mean(reported_fires["Time to Report [s]"]),
#         'median detect (s)': np.median(reported_fires["Time to Detect [s]"]),
#         'median report (s)': np.median(reported_fires["Time to Report [s]"]),
#         'mode detect (s)': stats.mstats.mode(reported_fires["Time to Detect [s]"])[0][0],
#         'mode report (s)': stats.mstats.mode(reported_fires["Time to Report [s]"])[0][0],
#         'standard deviation detect (s)': np.std(reported_fires["Time to Detect [s]"]),
#         'standard deviation report (s)': np.std(reported_fires["Time to Report [s]"]),
#         '25th percentile detect (s)': np.percentile(reported_fires["Time to Detect [s]"],25),
#         '25th percentile report (s)': np.percentile(reported_fires["Time to Report [s]"],25),
#         '75th percentile detect (s)': np.percentile(reported_fires["Time to Detect [s]"],75),
#         '75th percentile report (s)': np.percentile(reported_fires["Time to Report [s]"],75),
#     }
