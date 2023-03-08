# -*- coding: utf-8 -*-
"""
    *This application outputs processed utility and cost curves for each individual event*
"""
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from operator import truediv
import numpy as np

sat_stats = pd.read_csv('examples/utility/outputs/daythreetest.csv',encoding='utf8',skiprows=10)
leng = len(sat_stats)
constantCost = 18.5

lenArray = []
l=0

#Make new col for individual durations
newCol = []
count = 0
while l < leng:
    lenArray.append((pd.to_datetime(sat_stats["finish"][l]) - pd.to_datetime(sat_stats["start"][l])).days)
    sd_ser = pd.Series(sat_stats["detected"][l].replace("[","").replace("]","").split("), "))
    xaxis = []
    detbylabel = []
    for x in sd_ser:
        for f in ("datetime.datetime(%Y, %m, %d, %H, %M, %S, tzinfo=datetime.timezone.utc","datetime.datetime(%Y, %m, %d, %H, %M, tzinfo=datetime.timezone.utc", "datetime.datetime(%Y, %m, %d, %H, %M, %S, tzinfo=datetime.timezone.utc)", "datetime.datetime(%Y, %m, %d, %H, %M, tzinfo=datetime.timezone.utc"):
            try:
                xaxis.append(pd.to_datetime(datetime.strptime(x, f)))
            except ValueError:
                pass
    ser_xax = pd.Series(xaxis)
    newCol.append(xaxis)
    l = l+1

sat_stats["durTimeX"] = newCol

#Make new col for detection names
newColdb = []
l=0
while l < leng:
    db_ser = sat_stats["detected_by"][l].replace("[","").replace("]","").replace("'","").split(", ")
    newColdb.append(db_ser)
    l = l+1

sat_stats["detLabel"] = newColdb

#TIME FUNCTIONS: Make new col for utility 
newColUtil = []
newColTrial2 = []
l=0
while l < leng:
    utils = []
    trial2 = []
    for p in sat_stats["durTimeX"][l]:
        dif = (pd.to_datetime(p)) - pd.to_datetime(sat_stats["start"][l]).replace(tzinfo=None)
        dif = dif.total_seconds()
        if dif < 0:
            val = 0
            utils.append(val)
        elif dif > 0 and dif < 86400:
            val = (dif * 10) / 100000 /10
            utils.append(val)
            trial2.append(val)
        elif dif >= 86400 and dif < 172800:
            val = 1000000/100000 / 10
            utils.append(val)
            trial2.append(val)
        elif dif >= 172800 and dif < 259200:
            val =  (1000000 - 10 * (dif - 172799)) / 100000 /10
            utils.append(val)
            trial2.append(val)
        else:
            val = 0
            utils.append(val)
    ser_utils = pd.Series(utils)
    newColUtil.append(ser_utils)
    newColTrial2.append(sum(trial2) / len(trial2))
    l = l+1

sat_stats["scienceUtil"] = newColUtil
sat_stats["evAv"] = newColTrial2


#Calc util for A and B, and cost for A specifically
l = 0
newColUtilA = []
newColUtilB = []
newColCostsA = []

while l < leng:
    uA = []
    uB = []
    costsA = []
    for d in sat_stats["detLabel"][l]:
        if d[0] == "C":
            try: 
                i = sat_stats["detLabel"][l].index(d)
                uA.append(sat_stats["scienceUtil"][l][i])
                dif = (pd.to_datetime(sat_stats["durTimeX"][l][i])) - pd.to_datetime(sat_stats["start"][l]).replace(tzinfo=None)
                dif = dif.total_seconds()
                if dif < 0:
                    c = 1
                    costsA.append(c)
                elif dif >= 0 and dif < 72000:
                    c = 10
                    costsA.append(c)
                elif dif >= 72000 and dif < 144000:
                    c = 15
                    costsA.append(c)
                elif dif >= 144000 and dif < 216000:
                    c = 20
                    costsA.append(c)
                else:
                    c = 1
                    costsA.append(c)
                ser_costsA = pd.Series(costsA)
            except:
                pass
        else:
            try: 
                j = sat_stats["detLabel"][l].index(d)
                uB.append(sat_stats["scienceUtil"][l][j])
            except:
                pass
    newColUtilA.append(uA)
    newColUtilB.append(uB)
    newColCostsA.append(ser_costsA)
    l = l + 1

sat_stats["utilA"] = newColUtilA
sat_stats["utilB"]=  newColUtilB
sat_stats["costsA"] = newColCostsA


#make averages
l = 0
newColavgA = []
newColavgB = []

while l < leng:
    try:
        aA = (sum(sat_stats["utilA"][l]) / len(sat_stats["utilA"][l]))
    except:
        aA = 0
    try:
        aB = (sum(sat_stats["utilB"][l])  / len(sat_stats["utilB"][l]))
    except:
        aB = 0
    
    newColavgA.append(aA)
    newColavgB.append(aB)
    l = l + 1

sat_stats["avgA"] = newColavgA
sat_stats["avgB"]=  newColavgB


#calculate ratio
l = 0
newColratA = []
newColratB = []
ratavgA = []

while l < leng:
    newColratB.append(sat_stats["avgB"][l] / constantCost)
    newColratA.append([i / j for i, j in zip(sat_stats["utilA"][l], sat_stats["costsA"][l])])
    ratavgA.append(sum(newColratA[l])/len(newColratA[l]))
    l = l + 1

sat_stats["ratA"] = ratavgA
sat_stats["ratB"]=  newColratB

#Calculate Summary Results
#~~~~~~~~~~~~~~~~~~~~~~~~~

#Calculate if A or B has better ratios
l = 0
countA = 0
countB = 0
avgtotA = 0
avgtotB = 0
while l < leng:
    avgtotA = avgtotA + sat_stats["ratA"][l] 
    avgtotB = avgtotB + sat_stats["ratB"][l] 
    if (sat_stats["ratA"][l] - sat_stats["ratB"][l]) > 0:
        countA = countA + 1
    else:
        countB = countB + 1
    l = l + 1

print("A: " + str(countA))
print("B: " + str(countB))
print("A Avg: " + str(avgtotA / l))
print("B Avg: " + str(avgtotB / l))

#Calculate if mission is effective
l = 0
baseline = .5
count = 0
while l < leng:
    if sat_stats["evAv"][l] >= baseline:
        count = count + 1
    l = l+1

print("Number of Events With Average Detection Above Baseline:" + str(count))

sat_stats.sort_values("durTimeX")
#Plot graphs
#l=0
fig = make_subplots()
#while l < leng:
#    fig.add_trace(go.Scatter(x=sat_stats["durTimeX"][l], y = sat_stats["scienceUtil"][l],mode = "markers", text= "Provider A Sat 11", name = ("Event " + str(l))))
#    l = l+1   

fig.add_trace(go.Scatter(x=sat_stats["eventId"], y = sat_stats["evAv"],mode = "markers"))
fig.add_hrect(y0=baseline, y1=1, line_width=0, fillcolor="green", opacity=0.2)                                                   

#Cost A
#fig.add_trace(
#    go.Scatter(x=['2022-11-01 6:00:00', '2022-11-02 00:00:00','2022-11-02 00:00:00', '2022-11-03 0:00:00','2022-11-03 0:00:00', '2022-11-03 18:00:00'], y=[20, 20, 15, 15, 10, 10], name = "Cost A"),
#)

#Cost B
#fig.add_trace(
#    go.Scatter(x=['2022-11-01 6:00:00', '2022-11-03 18:00:00'], y=[constantCost, constantCost], name = "Cost B"),
#)

fig.update_yaxes(title="Average Science Value")
#fig.update_yaxes(secondary_y= True, title="Utility Value (units)")
#fig.update_yaxes(title="Science Value")
fig.update_xaxes(title="Event Number")
#fig.update_layout(title="Three Day Science Event Value Graph for Commerical Satellite Tasking")
fig.update_layout(title="Three Day Science Event Average Value Graph")

#fig.add_annotation(
#    text = ("Number of events best processed by Provider A: " + str(countA) + "<br>" + "Number of events best processed by Provider B: " + str(countB)), showarrow=False, x = 0, y = -0.15, xref='paper', yref='paper' , xanchor='left'
#    , yanchor='bottom', xshift=-1, yshift=-5, font=dict(size=10, color="grey"), align="left",)

#fig.add_annotation(
#    text = ("Average Value for Provider A:" + str(avgtotA / l) + "<br>" + "Average Value for Provider B:" + str(avgtotB / l)), x = 50, y = -0.15, showarrow=False, xref='paper', yref='paper' , xanchor='left'
#    , yanchor='bottom', xshift=-1, yshift=-5, font=dict(size=10, color="grey"), align="left",)

fig.add_annotation(
    text = ("Number of Events With Average Detection Above Baseline: " + str(count)), showarrow=False, x = 0, y = -0.15, xref='paper', yref='paper' , xanchor='left'
    , yanchor='bottom', xshift=-1, yshift=-5, font=dict(size=10, color="grey"), align="left",)


fig.show()