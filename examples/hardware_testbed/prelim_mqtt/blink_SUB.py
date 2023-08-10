import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time
from time import sleep
from dotenv import dotenv_values
from config import PREFIX

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)

credentials = dotenv_values(".env")
SMCE_HOST, SMCE_PORT = credentials["SMCE_HOST"], int(credentials["SMCE_PORT"])
SMCE_USERNAME, SMCE_PASSWORD = credentials["SMCE_USERNAME"], credentials["SMCE_PASSWORD"]

TPC = f"{PREFIX}/hrdwr/blinkLED"

def on_connect(CLIENT, userdata, flags, rc):
    print("Connected with code " + str(rc))
    CLIENT.subscribe(TPC)
    print("Connected to the following topics: " + TPC)

def on_message(CLIENT, userdata, msg):
    message = msg.payload.decode("utf-8")
    if msg.topic == TPC and message == "sunlit":
        GPIO.output(11, GPIO.HIGH)
        print("ISS is sunlit")
    else:
        GPIO.output(11, GPIO.LOW)
        print("ISS is in shadow")
                
# build the MQTT CLIENT
CLIENT = mqtt.Client()
# set CLIENT username and password
CLIENT.username_pw_set(username=SMCE_USERNAME, password=SMCE_PASSWORD)
# set tls certificate
CLIENT.tls_set()

CLIENT.on_connect = on_connect
CLIENT.on_message = on_message

# connect to MQTT server on port 8883
CLIENT.connect(SMCE_HOST, SMCE_PORT)
CLIENT.loop_forever()
