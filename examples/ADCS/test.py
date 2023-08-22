# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 10:37:11 2023

@author: brian
"""
import datetime
import time
import pandas as pd
       
datalist = []
dict1 = {"time":[],"rollangle":[]}
datadict = {"time":[],"rollangle":[]}
rollangle = 0

def add_to_rollangle(rollangle):
    rollangle=rollangle+1
    x = [1,2,3]
    datadict["rollangle"].append(x)
    
def get_time():
    datadict["time"].append(datetime.datetime.now())

for x in range(1,15):
    add_to_rollangle(rollangle)
    get_time()
    # x = {"time":datetime.datetime.now(), "rollangle":rollangle}
    # datalist.append(x)
    
    
    time.sleep(0.1)