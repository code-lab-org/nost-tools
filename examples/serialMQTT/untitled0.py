"""mqtt_serial_bridge.py
Command-line utility to connect a serial-port device with a remote MQTT server.
Please note: the Configuration settings must be customized before us.
"""

################################################################
# Configuration

# The following variables must be customized to set up the network and serial
# port settings.

# NOS-T MQTT server name.
mqtt_hostname = "testbed.mysmce.com"

# MQTT Port with TLS
mqtt_portnum  = 8883

# Username and password
mqtt_username = 'mlevine4_Operator'
mqtt_password = 'operator2023'

# MQTT publication topic
mqtt_topic = 'serial/arduino/state'

# MQTT receive subscription
mqtt_subscription = 'serial/event/trigger'

# Serial port device to bridge to the network (e.g. Arduino).
# On Windows, this will usually be similar to 'COM5'.
# On macOS, this will usually be similar to '/dev/cu.usbmodem333101'
serial_portname = 'COM5'

################################################################
################################################################
# Written in 2018-2021 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################
# Import standard Python libraries.
import sys, time, signal

# Import the MQTT client library.
# documentation: https://www.eclipse.org/paho/clients/python/docs/
import paho.mqtt.client as mqtt

# Import the pySerial library.
# documentation: https://pyserial.readthedocs.io/en/latest/
import serial

################################################################
# Global script variables.

serial_port = None
client = None

################################################################
if mqtt_username == '' or mqtt_password == '' or mqtt_topic == '' or serial_portname == '': 
    print("""\
This script must be customized before it can be used.  Please edit the file with
a Python or text editor and set the variables appropriately in the Configuration
section at the top of the file.
""")
    if serial_portname == '':
        import serial.tools.list_ports
        print("All available serial ports:")
        for p in serial.tools.list_ports.comports():
            print(" ", p.device)
    sys.exit(0)

################################################################
# Attach a handler to the keyboard interrupt (control-C).
def _sigint_handler(signal, frame):
    print("Keyboard interrupt caught, closing down...")
    if serial_port is not None:
        serial_port.close()

    if client is not None:
        client.loop_stop()
        
    sys.exit(0)

signal.signal(signal.SIGINT, _sigint_handler)        
################################################################
# MQTT networking functions.

#----------------------------------------------------------------
# The callback for when the broker responds to our connection request.
def on_connect(client, userdata, flags, rc):
    print(f"MQTT connected with flags: {flags}, result code: {rc}")

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    # The hash mark is a multi-level wildcard, so this will subscribe to all subtopics of 16223
    client.subscribe(mqtt_subscription)
    return
#----------------------------------------------------------------
# The callback for when a message has been received on a topic to which this
# client is subscribed.  The message variable is a MQTTMessage that describes
# all of the message parameters.

# Some useful MQTTMessage fields: topic, payload, qos, retain, mid, properties.
#   The payload is a binary string (bytes).
#   qos is an integer quality of service indicator (0,1, or 2)
#   mid is an integer message ID.
def on_message(client, userdata, msg):
    print(f"message received: topic: {msg.topic} payload: {msg.payload}")

    # If the serial port is ready, re-transmit received messages to the
    # device. The msg.payload is a bytes object which can be directly sent to
    # the serial port with an appended line ending.
    if serial_port is not None and serial_port.is_open:
        serial_port.write(msg.payload + b'\n')
    return

#----------------------------------------------------------------
# Launch the MQTT network client
client = mqtt.Client()
client.enable_logger()
client.on_connect = on_connect
client.on_message = on_message
client.tls_set()
client.username_pw_set(mqtt_username, mqtt_password)

# Start a background thread to connect to the MQTT network.
client.connect_async(mqtt_hostname, mqtt_portnum)
client.loop_start()

################################################################
# Connect to the serial device.
serial_port = serial.Serial(serial_portname, baudrate=115200, timeout=2.0)

# wait briefly for the Arduino to complete waking up
time.sleep(0.2)

print(f"Entering Arduino event loop for {serial_portname}.  Enter Control-C to quit.")

while(True):
    input = serial_port.readline().decode(encoding='ascii',errors='ignore').rstrip()
    if len(input) == 0:
        print("Serial device timed out, no data received.")
    else:
        print(f"Received from serial device: {input}")
        if client.is_connected():
            client.publish(topic=mqtt_topic, payload=input)