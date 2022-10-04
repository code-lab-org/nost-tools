import os
from skyfield.api import load

PREFIX = os.getenv("PREFIX", "greenfield")
NAME = "capella"
LOG = f"\x1b[1m[\x1b[34m{NAME}\x1b[37m]\x1b[0m"
HEADER = {
    "name": NAME,
    "description": "Capella constellation of SAR imagery satellites broadcast location on utility/satellite/location, and detect and report events on greenfield/satellite/detected and greenfield/satellite/reported. Subscribes to greenfield/fire/location.",
}

TLE1_SC1 = str(os.getenv(
    "TLE1", "1 43791U 18099AK  22270.14139052  .00078876  00000+0  35307-2 0  9994"))  #CAPELLA-1-DENALI
TLE2_SC1 = str(os.getenv(
    "TLE2", "2 43791  97.6648 350.2925 0008124 273.9924  86.0382 15.20919853208957"))  #CAPELLA-1-DENALI
TLE1_SC2 = str(os.getenv(
    "TLE1", "1 46269U 20060B   22269.26820173  .00038223  00000+0  13944-2 0  9995"))  #CAPELLA-2-SEQUOIA
TLE2_SC2 = str(os.getenv(
    "TLE2", "2 46269  45.1048 253.9885 0003171 102.6606 257.5599 15.27581222114614"))  #CAPELLA-2-SEQUOIA
TLE1_SC3 = str(os.getenv(
    "TLE1", "1 47489U 21006CE  22270.21025487  .00049839  00000+0  17384-2 0  9990"))  #CAPELLA-3-WHITNEY
TLE2_SC3 = str(os.getenv(
    "TLE2", "2 47489  97.4376 330.6681 0005132 267.5526  92.5127 15.29441178 92886"))  #CAPELLA-3-WHITNEY
TLE1_SC4 = str(os.getenv(
    "TLE1", "1 47481U 21006BW  22270.13675697  .00007629  00000+0  28938-3 0  9996"))  #CAPELLA-4-WHITNEY
TLE2_SC4 = str(os.getenv(
    "TLE2", "2 47481  97.4370 330.4456 0005732 270.3249  89.7333 15.27134028 92877"))  #CAPELLA-4-WHITNEY
TLE1_SC5 = str(os.getenv(
    "TLE1", "1 48913U 21059AL  22270.37287523  .00032885  00000+0  11923-2 0  9995"))  #CAPELLA-5-WHITNEY
TLE2_SC5 = str(os.getenv(
    "TLE2", "2 48913  97.5538  42.2699 0007228  99.7911 260.4145 15.28261061 69583"))  #CAPELLA-5-WHITNEY
TLE1_SC6 = str(os.getenv(
    "TLE1", "1 48605U 21041BE  22270.63872677  .00001526  00000+0  15083-3 0  9993"))  #CAPELLA-6-WHITNEY
TLE2_SC6 = str(os.getenv(
    "TLE2", "2 48605  53.0349  58.8228 0012770 356.2622   3.8265 14.97711654 74892"))  #CAPELLA-6-WHITNEY
TLE1_SC7 = str(os.getenv(
    "TLE1", "1 51072U 22002CS  22270.19479997  .00001741  00000+0  10575-3 0  9992"))  #CAPELLA-7-WHITNEY
TLE2_SC7 = str(os.getenv(
    "TLE2", "2 51072  97.4696 335.6758 0012914  99.8603 260.4086 15.11716819 38824"))  #CAPELLA-7-WHITNEY
TLE1_SC8 = str(os.getenv(
    "TLE1", "1 51071U 22002CR  22270.28217528  .00004521  00000+0  26467-3 0  9997"))  #CAPELLA-8-WHITNEY
TLE2_SC8 = str(os.getenv(
    "TLE2", "2 51071  97.4777 335.8824 0010902  81.7532 278.4934 15.12272297 38846"))  #CAPELLA-8-WHITNEY
TLES = [[TLE1_SC1,TLE2_SC1],[TLE1_SC2,TLE2_SC2],[TLE1_SC3,TLE2_SC3],[TLE1_SC4,TLE2_SC4],[TLE1_SC5,TLE2_SC5],[TLE1_SC6,TLE2_SC6],[TLE1_SC7,TLE2_SC7],[TLE1_SC8,TLE2_SC8]]

FIELD_OF_REGARD = [float(os.getenv("FIELD_OF_REGARD", 112.56)),
    float(os.getenv("FIELD_OF_REGARD", 112.56)),
    float(os.getenv("FIELD_OF_REGARD", 112.56)),
    float(os.getenv("FIELD_OF_REGARD", 112.56)),
    float(os.getenv("FIELD_OF_REGARD", 112.56)),
    float(os.getenv("FIELD_OF_REGARD", 112.56)),
    float(os.getenv("FIELD_OF_REGARD", 112.56)),
    float(os.getenv("FIELD_OF_REGARD", 112.56))
]  # degrees (found max zenith angle for MODIS is 65-degrees, FoR = 2 * zenith angle, field-of-view for VIIRS = 112.56-degrees)
# MIN_ELEVATION_COMMS = float(
#     os.getenv("MIN_ELEVATION_COMMS", 5.0)
# )  # degrees (comms more forgiving than sensor, not currently used)
# MIN_INTENSITY = float(os.getenv("MIN_INTENSITY", 10.0))  # square meters

SCALE = 60							
