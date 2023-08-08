import RPi.GPIO as GPIO
import time
from time import sleep
import json
from dotenv import dotenv_values
import paho.mqtt.client as mqtt

from config import (
    PREFIX,
    TPC
    )

LED_pin = 11
json_data = None

def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LED_pin, GPIO.OUT)
    GPIO.output(LED_pin, GPIO.LOW)
    
def on_connect(CLIENT, userdata, flags, rc):
    CLIENT.subscribe(TPC)
        
def on_message(CLIENT, userdata, msg):
    global json_data
    global LED_pin
    json
    comm_range = json_data.get("commRange")
    
    if comm_range:
        GPIO.output(LED_pin, GPIO.HIGH)
    else:
        GPIO.output(LED_pin, GPIO.LOW)
    
def mqtt_init():
    CLIENT = mqtt.Client()
    CLIENT.username_pw_set(username=USERNAME, password=PASSWORD)
    CLIENT.tls_set()
    CLIENT.on_connect = on_connect
    CLIENT.on_message = on_message
    CLIENT.connect(HOST,PORT)
    print(f"Successfully connected to {HOST} on topic(s) {TPC}")
    CLIENT.loop_forever()
    
if __name__ == '__main__':
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]
    setup()
    mqtt_init()
    
GPIO.cleanup()
