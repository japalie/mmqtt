import argparse
import time
import sys
from types import SimpleNamespace
from typing import Tuple

from mmqtt.load_config import ConfigLoader
from mmqtt.utils import validate_lat_lon_alt, str_with_empty
from mmqtt.tx_message_handler import (
    send_position,
    send_text_message,
    send_nodeinfo,
    send_device_telemetry,
    send_power_metrics,
    send_environment_metrics,
)


def get_args() -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
    """Define and parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Meshtastic MQTT client")

    parser.add_argument('--config', type=str, default='config.json', help='Path to the config file')
    # Node and Channel Settings
    parser.add_argument('--node_id', type=str, help='Node ID beginning with !')
    parser.add_argument('--node_long_name', type=str, help='Node name')
    parser.add_argument('--node_short_name', type=str, help='Node Short name')
    parser.add_argument('--node_role', type=str, help='Role of Node (CLIENT,REPEATER,ROUTER,TRACKER,SENSOR)')
    parser.add_argument('--node_hw_model', type=int, help='Hardware model number (255 is PRIVATEHW)')
    parser.add_argument('--node_is_unmessagable', type=bool, help='Node is unmessagable (True / False)')
    parser.add_argument('--channel_preset', type=str, help='Channel Name')
    parser.add_argument('--channel_key', type=str_with_empty, help='Channel Encryption Key (Default: AQ==)')
    parser.add_argument('--destination', type=int, help='Destination Node Number (4294967295 is Broadcast)')
    parser.add_argument('--hop_limit', type=int, help='Set hop-limit default: 3 (max: 7)')
    parser.add_argument('--priority', type=str, help='Message Priority (UNSET/MIN/BACKGROUND/DEFAULT/RALIABLE/HIGH/MAX)')
    # Send Message
    parser.add_argument('--message', action='append', help='Message(s) to send. You can use this multiple times.')
    parser.add_argument('--message-file', type=str, help='Path to a file containing messages, one per line')
    # NodeInfo
    parser.add_argument('--nodeinfo', action='store_true', help='Send NodeInfo from config')
    # Device Telemetry Data
    parser.add_argument('--battery', type=int, help='Battery level (0-101, 101 = PSU)')
    parser.add_argument('--voltage', type=float, help='Battery Voltage (0.0 - 99.9)')
    parser.add_argument('--chutil', type=float, help='Channel utilization (0.0 - 100.0)')
    parser.add_argument('--airtxutil', type=float, help='Airtime (0.0 - 100.0)')
    parser.add_argument('--uptime', type=int, help='Uptime in seconds')
    parser.add_argument('--telemetry', action='store_true', help='Send Device telemetry from config or overridden by --battery/voltage/chutil/airtxutil/uptime')
    # Position Data
    parser.add_argument('--lat', type=float, help='Latitude coordinate')
    parser.add_argument('--lon', type=float, help='Longitude coordinate')
    parser.add_argument('--alt', type=float, help='Altitude')
    parser.add_argument('--precision', type=int, help='Position Precision')
    parser.add_argument('--position', action='store_true', help='Send position from config or overridden by --lat/lon/alt')
    # Environment Data
    parser.add_argument('--temperature', type=float, help='Temperature in °C - float')
    parser.add_argument('--humidity', type=float, help='Relative Humidity (0.0 - 100.0 %%RH)')
    parser.add_argument('--pressure', type=float, help='Barometric Pressure in hPa - float')
    parser.add_argument('--lux', type=float, help='Illuminance in lux - float')
    parser.add_argument('--wind_dir', type=int, help='Wind direction in degrees 360=North')
    parser.add_argument('--wind_speed', type=float, help='Wind Speed in m/s - float')
    parser.add_argument('--weight', type=float, help='Weight in kg - float')
    parser.add_argument('--radiation', type=float, help='Radiation in µR/h (microroentgen/hour) - float')
    parser.add_argument('--environment', action='store_true', help='Send environment from config or overridden by --temperature/humidity/pressure/lux/wind_dir/wind_speed/weight/radiation')
    # Power Data
    parser.add_argument('--ch1_voltage', type=float, help='CH1 Voltage in V - float')
    parser.add_argument('--ch1_current', type=float, help='CH1 Current in mA - float')
    parser.add_argument('--ch2_voltage', type=float, help='CH2 Voltage in V - float')
    parser.add_argument('--ch2_current', type=float, help='CH2 Current in mA - float')
    parser.add_argument('--ch3_voltage', type=float, help='CH3 Voltage in V - float')
    parser.add_argument('--ch3_current', type=float, help='CH3 Current in mA - float')
    parser.add_argument('--power', action='store_true', help='Send power from config or overridden by --ch1_voltage/ch1_current/ch2_voltage/ch2_current/ch3_voltage/ch3_current')
    # Start Listener
    parser.add_argument('--listen', action='store_true', help='Enable listening for incoming MQTT messages')
    # parser.add_argument('--use-args', action='store_true', help='Use values from config.json instead of client attributes')

    args = parser.parse_args()
    return parser, args


def handle_args() -> argparse.Namespace:
    """
    Process and handle CLI arguments to trigger various MQTT message actions.
    Returns:
        argparse.Namespace: Parsed argument namespace
    """
    parser, args = get_args()
    config: SimpleNamespace = ConfigLoader.get_config(args.config)
    
    arg_order = sys.argv[1:]
    
    messages = args.message or []
    
    channel_key = ""
    if args.channel_key is None:
        channel_key = None
    elif args.channel_key == "":
        channel_key = ''
    else:
        channel_key = args.channel_key
    
    _overrides = {
        "node_id": getattr(args, 'node_id', None) or None,
#        "node_long_name": getattr(args, 'node_long_name', None) or None,
#        "node_short_name": getattr(args, 'node_short_name', None) or None,
#        "node_hw_model": getattr(args, 'node_hw_model', None) or None,
        "channel_preset": getattr(args, 'channel_preset', None) or None,
        "channel_key": channel_key,
        "destination": getattr(args, 'destination', None) or None,
        "hop_limit": getattr(args, 'hop_limit', None) or None,
        "priority": getattr(args, 'priority', None) or None,
    }

    for arg in arg_order:
        if arg == "--nodeinfo" and args.nodeinfo:
            node = config.nodeinfo           
            #send_nodeinfo(node.id, node.long_name, node.short_name)
            send_nodeinfo(
                id = getattr(args, 'node_id', None) or getattr(node, 'id', None) or None,
                long_name = getattr(args, 'node_long_name', None) or getattr(node, 'long_name', None) or None,
                short_name = getattr(args, 'node_short_name', None) or getattr(node, 'short_name', None) or None,
                hw_model = getattr(args, 'node_hw_model', None) or getattr(node, 'hw_model', None) or None,
                role = getattr(args, 'node_role', None) or getattr(node, 'role', None) or None,
                is_unmessagable = getattr(args, 'node_is_unmessagable', None) or getattr(node, 'is_unmessagable', None) or None,
                use_config = True,
                _overrides = _overrides
            )
            time.sleep(3)
            
        elif arg == "--message" and messages:
            for msg in messages:
                send_text_message(msg, use_config=True, _overrides = _overrides)
                time.sleep(3)
            messages = []  # prevent duplicate sending

        elif arg == "--message-file" and args.message_file:
            try:
                with open(args.message_file, 'r', encoding='utf-8') as f:
                    file_lines = [line.strip() for line in f if line.strip()]
                    for msg in file_lines:
                        send_text_message(msg, use_config=True)
                        time.sleep(3)
            except FileNotFoundError:
                print(f"Message file '{args.message_file}' not found.")

        elif arg == "--position" and args.position:
            position = config.position
            lat = args.lat if args.lat is not None else position.lat
            lon = args.lon if args.lon is not None else position.lon
            alt = args.alt if args.alt is not None else position.alt
            precision = args.precision if args.precision is not None else position.precision
            validate_lat_lon_alt(parser, argparse.Namespace(lat=lat, lon=lon, alt=alt))
            send_position(lat, lon, alt, precision, use_config=True, _overrides = _overrides)
            time.sleep(3)

        elif arg == "--telemetry" and args.telemetry:
            telemetry = config.telemetry
            
            send_device_telemetry(
                battery_level = getattr(args, 'battery', None) or getattr(telemetry, 'battery_level', None) or None,
                voltage = getattr(args, 'voltage', None) or getattr(telemetry, 'voltage', None) or None,
                channel_utilization = getattr(args, 'channel_utilization', None) or getattr(telemetry, 'chutil', None) or getattr(telemetry, 'channel_utilization', None) or None,
                air_util_tx = getattr(args, 'air_util_tx', None) or getattr(telemetry, 'airtxutil', None) or getattr(telemetry, 'air_util_tx', None) or None,
                uptime_seconds = getattr(args, 'uptime_seconds', None) or getattr(telemetry, 'uptime', None) or getattr(telemetry, 'uptime_seconds', None) or None,
                use_config=True,
                _overrides = _overrides
            )
            time.sleep(3)

        elif arg == "--environment" and args.environment:
            environment = config.environment
            send_environment_metrics(
                temperature = getattr(args, 'temperature', None) or getattr(environment, 'temperature', None) or None,
                relative_humidity = getattr(args, 'humidity', None) or getattr(environment, 'humidity', None) or None,
                barometric_pressure = getattr(args, 'pressure', None) or getattr(environment, 'pressure', None) or None,
                lux = getattr(args, 'lux', None) or getattr(environment, 'lux', None) or None,
                wind_direction = getattr(args, 'wind_dir', None) or getattr(environment, 'wind_direction', None) or None,
                wind_speed = getattr(args, 'wind_speed', None) or getattr(environment, 'wind_speed', None) or None,
                weight = getattr(args, 'weight', None) or getattr(environment, 'weight', None) or None,
                radiation = getattr(args, 'radiation', None) or getattr(environment, 'radiation', None) or None,
                use_config=True,
                _overrides = _overrides
            )
            time.sleep(3)
            
        elif arg == "--power" and args.power:
            power = config.power
            send_power_metrics(
                ch1_voltage = getattr(args, 'ch1_voltage', None) or getattr(power, 'ch1_voltage', None) or None,
                ch1_current = getattr(args, 'ch1_current', None) or getattr(power, 'ch1_current', None) or None,
                ch2_voltage = getattr(args, 'ch2_voltage', None) or getattr(power, 'ch2_voltage', None) or None,
                ch2_current = getattr(args, 'ch2_current', None) or getattr(power, 'ch2_current', None) or None,
                ch3_voltage = getattr(args, 'ch3_voltage', None) or getattr(power, 'ch3_voltage', None) or None,
                ch3_current = getattr(args, 'ch3_current', None) or getattr(power, 'ch3_current', None) or None,
                use_config=True,
                _overrides = _overrides
            )
            time.sleep(3)

    # Listen Mode
    if args.listen:
        from mmqtt import client
        client.enable_verbose(True)
        config.listen_mode = True
        
        print("Starting MQTT listener (press Ctrl+C to stop)...")

        client.subscribe()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting listener.")
            client.disconnect()

    return args
