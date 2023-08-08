from wificonfig import ssid, password

import network
from time import sleep

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

if wlan.isconnected == False:
    sleep(0.5)

print("Successfully Connected to " + ssid)