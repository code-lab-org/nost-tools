from machine import Pin
from wificonfig import *
from umqtt.robust import MQTTClient
import lowpower

import utime
import network

#PIN CONFIGURATION
IR_PIN = 6
DEBOUNCE_MS = 200
mqttLED_PIN = 16
CONFIRM_PIN = 17
PICOCLIENT = "Pico_SUOMI"
CLIENT = MQTTClient(client_id=PICOCLIENT, server=HOST, port=PORT, user=USERNAME, password=PASSWORD, ssl=True)

mqttLED = Pin(mqttLED_PIN, Pin.OUT)
confirmLED = Pin(CONFIRM_PIN, Pin.OUT)
standby = Pin("LED", Pin.OUT)

def wifi_connect():
    global wlan
    wlan = network.WLAN(network.STA_IF)
    #print("Connecting to WiFi...")
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        pass
    print("Connected to WiFi:", ssid)
    standby.on()

def mqtt_connect():
    try:
        CLIENT.set_callback(on_message)
        CLIENT.connect()
        CLIENT.subscribe(SAT_TPC4)
        print('Connected to', HOST, "on topic", SAT_TPC4)
        mqttLED.on()
    except Exception as e:
        print("MQTT: ERROR connecting to broker:", e)
    
def on_message(topic, msg):
    try:
        print("Received message on topic:", topic)
        confirmLED.on()
    except Exception as e:
        print("Exception in on_message:", e)


last_button_time = 0

def ir_handler(pin):
    global in_low_power_mode, ir_received, last_button_time
    current_time = utime.ticks_ms()
    if current_time - last_button_time >= DEBOUNCE_MS:
        last_button_time = current_time
        ir_received = True
        in_low_power_mode = False

ir = Pin(IR_PIN, Pin.IN, Pin.PULL_UP)
ir.irq(handler=ir_handler, trigger=Pin.IRQ_FALLING)

print("Entering low-power mode...")
in_low_power_mode = True
ir_received = False
standby.off()
mqttLED.off()
confirmLED.off()
lowpower.lightsleep()

exiting_low_power_mode = False

while True:
    if not in_low_power_mode:
        if ir_received:
            print("Exiting low-power mode...")
            wifi_connect()
            mqtt_connect()
            ir_received = False
            exiting_low_power_mode = False
            last_received = utime.ticks_ms()
        else:
            current_time = utime.ticks_ms()
            if current_time - last_received >= 20000:
                print("Entering low-power mode...")
                mqttLED.off()
                standby.off()
                confirmLED.off()
                CLIENT.disconnect()
                wlan.disconnect()
                in_low_power_mode = True
                lowpower.lightsleep()
            else:
                CLIENT.check_msg()
                utime.sleep_ms(100)
    else:
        standby.off()
        mqttLED.off()
        confirmLED.off()
        lowpower.lightsleep()
