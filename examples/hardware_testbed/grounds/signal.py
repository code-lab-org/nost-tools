import math
import scipy

from scipy import constants
from config import *
from main_ground import distance_from_grnd

c = constants.speed_of_light

lambda_uplink = c / (uplink*1000000)

def fspl(distance):
    result = ((4 * math.pi * (distance*1000))/lambda_uplink)**2
    return result
