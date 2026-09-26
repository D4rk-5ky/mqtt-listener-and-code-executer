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

            # A mapping is one complete payload and one shell command. Parse it
            # before section headers so a command ending in ':' stays intact.
            if section == 'commands' and '=' in line:
                cmd_key, cmd_value = line.split('=', 1)
                commands[cmd_key.strip()] = cmd_value.strip()
                continue

            if line.endswith(':'):
                section = line[:-1].strip()
                if section == 'commands':
                    config['commands'] = commands
                continue

            if ':' in line:
                key, value = line.split(':', 1)
                config[key.strip()] = value.strip()

    return config

# ---------------------------
# MQTT Callbacks
# ---------------------------
def get_online_topic(config, topics):
    """Reserve a separate publish topic, or leave legacy behavior unchanged."""
    topic = config.get('online_topic', '').strip()
    if not topic:
        return None
    if any(char in topic for char in ('+', '#', '\x00')) or len(topic.encode('utf-8')) > 65535:
        print('Online announcement disabled: online_topic must be a valid publish topic')
        return None
    if topic in topics:
        print('Online announcement disabled: online_topic must differ from command topics')
        return None
    return topic


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    for topic in userdata['topics']:
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

    # Do not wait for PUBACK here: callbacks run inside the MQTT network loop.
    online_topic = userdata.get('online_topic')
    if rc == 0 and online_topic:
        try:
            result = client.publish(online_topic, payload='online', qos=1, retain=False)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Queued online announcement on topic: {online_topic}")
            else:
                print(f"Online announcement could not be queued: {result.rc}")
        except Exception as e:
            print(f"Failed to announce online: {e}")


def on_message(client, userdata, msg):
    # MQTT 3 does not identify the publisher. Reserve this exact topic so a
    # wildcard subscription cannot turn our own announcement into a command.
    if userdata.get('online_topic') and msg.topic == userdata['online_topic']:
        return

    payload = msg.payload.decode().strip()
    print(f"Received message '{payload}' on topic '{msg.topic}'")

    # Match the whole payload, including internal spaces; never execute raw input.
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

    userdata = {'topics': topics, 'commands': commands}
    online_topic = get_online_topic(config, topics)
    if online_topic:
        userdata['online_topic'] = online_topic
    client = mqtt.Client(userdata=userdata)
    client.on_connect = on_connect
    client.on_message = on_message

    if username and password:
        client.username_pw_set(username, password)

    client.connect(hostname, port, 60)
    client.loop_forever()
