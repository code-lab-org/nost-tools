import machine
import utime
import json
import network
from machine import Pin
from umqtt.robust import MQTTClient
from wificonfig import *
from ds1302 import DS1302

standby = Pin("LED", Pin.OUT)
signal_led = Pin(16, Pin.OUT)
signal_led.off()

def standby_disconnect():
    for i in range(10):
        standby.on()
        utime.sleep(1)
        standby.off()
        utime.sleep(1)

def on_message(topic, msg):
    received_time = utime.ticks_ms()
    latency = received_time - start_time 

    offset = -4
    current_time = utime.localtime()
    current_time_adj = list(current_time)
    current_time_adj[3] += offset
    current_time_adj = tuple(current_time_adj)

    print("Latency for message: {} ms".format(latency))
    print("Current time: %02d:%02d:%02d" % current_time_adj[3:6])

    payload_size = len(msg) 
    print("Payload Size: {} bytes".format(payload_size))

rtc = DS1302(machine.Pin(0), machine.Pin(1), machine.Pin(2))

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while True:
    if not wlan.isconnected():
        utime.sleep(1)
        continue

    print("Successfully Connected to", ssid)
    TPC = SAT_TPC4
    PICOCLIENT = "Pico_SUOMI"

    CLIENT = MQTTClient(client_id=PICOCLIENT, server=HOST, port=PORT, user=USERNAME, password=PASSWORD, ssl=True)

    CLIENT.set_callback(on_message)
    CLIENT.connect()
    print('Connected to', HOST)
    CLIENT.subscribe(SAT_TPC4)

    try:
        print('Waiting for messages on', SAT_TPC4)
        while True:
            start_time = utime.ticks_ms()
            CLIENT.wait_msg()

    except Exception as e:
        print('Failed to wait for MQTT messages:')

