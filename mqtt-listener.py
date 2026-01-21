#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import subprocess
import argparse

# ---------------------------
# Config File Parsing
# ---------------------------
def read_config(file_path):
    config = {}
    commands = {}
    section = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.endswith(':'):
                section = line[:-1].strip()
                if section == 'commands':
                    config['commands'] = commands
                continue

            if section == 'commands' and '=' in line:
                cmd_key, cmd_value = line.split('=', 1)
                commands[cmd_key.strip()] = cmd_value.strip()
            elif ':' in line:
                key, value = line.split(':', 1)
                config[key.strip()] = value.strip()

    return config

# ---------------------------
# MQTT Callbacks
# ---------------------------
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    for topic in userdata['topics']:
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode().strip()
    print(f"Received message '{payload}' on topic '{msg.topic}'")

    command = userdata['commands'].get(payload)
    if command:
        try:
            # Use Popen to make sure the command doesn't block
            subprocess.Popen(command, shell=True)
            print(f"Executed command in background: {command}")
        except Exception as e:
            print(f"Failed to execute command: {e}")
    else:
        print(f"No command found for payload: '{payload}'")

# ---------------------------
# Main
# ---------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MQTT Listener with Command Execution')
    parser.add_argument('-c', '--config', required=True, help='Path to configuration file')
    args = parser.parse_args()

    config = read_config(args.config)

    hostname = config.get('hostname', 'localhost')
    port = int(config.get('port', 1883))
    username = config.get('username')
    password = config.get('password')
    topics = [t.strip() for t in config.get('topics', '').split(',')]
    commands = config.get('commands', {})

    client = mqtt.Client(userdata={'topics': topics, 'commands': commands})
    client.on_connect = on_connect
    client.on_message = on_message

    if username and password:
        client.username_pw_set(username, password)

    client.connect(hostname, port, 60)
    client.loop_forever()
