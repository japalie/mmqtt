#!/usr/bin/env python3
"""
Powered by Meshtastic™ https://meshtastic.org/
"""

import time
import paho.mqtt.client as mqtt

from tx_message_handler import send_nodeinfo, send_position, send_device_telemetry, send_text_message
from load_config import mqtt_broker, mqtt_port, mqtt_username, mqtt_password, lat, lon, alt, position_precision
from mqtt_handler import connect_mqtt
from argument_parser import handle_args

stay_connected = True


def main():
    client = connect_mqtt(mqtt_broker, mqtt_port, mqtt_username, mqtt_password)
    
    if handle_args(client) == None:

        send_nodeinfo(client)
        time.sleep(3)

        # send_position(client, lat=lat, lon=lon, alt=alt, pre=position_precision)
        # time.sleep(3)

        # send_device_telemetry(client, battery_level=99, voltage=4.0, chutil=3, airtxutil=1, uptime=420)
        # time.sleep(3)

        # send_text_message(client, "Happy New Year!")
        # time.sleep(3)

   
    if not stay_connected:
        client.disconnect()
    else:
        while True:
            time.sleep(1)

if __name__ == "__main__":
    main()