#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import subprocess
import argparse
import hashlib
import json
import re
from pathlib import Path

# Keep one version source for both the source release and the bundled executable.
VERSION = Path(__file__).resolve().with_name('VERSION').read_text(encoding='utf-8').strip()

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
    if not valid_publish_topic(topic):
        print('Online announcement disabled: online_topic must be a valid publish topic')
        return None
    if topic in topics:
        print('Online announcement disabled: online_topic must differ from command topics')
        return None
    return topic


def valid_publish_topic(topic):
    """Validate HA topic names before installing subscriptions or a Last Will."""
    return bool(topic) and not any(c in topic for c in ('+', '#', '\x00')) \
        and len(topic.encode('utf-8')) <= 65535


def get_home_assistant_config(config, topics, online_topic):
    """Build optional discovery settings; reject conflicts without changing commands."""
    enabled = config.get('ha_enabled', 'false').strip().lower()
    if enabled == 'false':
        return None
    try:
        if enabled != 'true':
            raise ValueError('ha_enabled must be true or false')
        device_id = config.get('ha_device_id', '').strip()
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}', device_id):
            raise ValueError('ha_device_id must contain 1-128 letters, digits, underscores or hyphens')
        name = config.get('ha_device_name', 'MQTT Command Listener').strip()
        if not name:
            raise ValueError('ha_device_name must not be blank')
        prefix = config.get('ha_discovery_prefix', 'homeassistant').strip().rstrip('/')
        command_topic = config.get('ha_command_topic', topics[0] if topics else '').strip()
        availability = config.get('ha_availability_topic',
                                  'mqtt-listener/' + device_id + '/availability').strip()
        status = config.get('ha_status_topic', 'homeassistant/status').strip()
        status_payload = config.get('ha_status_online_payload', 'online').strip()
        retain = config.get('ha_discovery_retain', 'true').strip().lower()
        if retain not in ('true', 'false') or not status_payload:
            raise ValueError('ha_discovery_retain must be true/false and HA birth payload nonempty')
        node_id = 'mqtt_listener_' + device_id
        discovery_base = prefix + '/button/' + node_id + '/'
        # Leave room for a SHA-256 button identifier and the /config suffix.
        if not all(valid_publish_topic(t) for t in
                   (prefix, command_topic, availability, status, discovery_base + '0' * 64 + '/config')):
            raise ValueError('HA topics must be nonempty publish topics without wildcards or nulls')
        if not any(mqtt.topic_matches_sub(topic, command_topic) for topic in topics):
            raise ValueError('ha_command_topic must be covered by an existing topics subscription')
        reserved = [availability, status] + ([online_topic] if online_topic else [])
        if len(set(reserved)) != len(reserved):
            raise ValueError('HA availability, HA birth and listener online topics must differ')
        if command_topic in reserved:
            raise ValueError('ha_command_topic must differ from all status and availability topics')
        if any(t in topics for t in (availability, status)):
            raise ValueError('HA availability and birth topics must differ from command topics')
        if any(t.startswith(discovery_base) for t in topics + reserved + [command_topic]):
            raise ValueError('command/status topics must be outside this device discovery namespace')
        return dict(device_id=node_id, device_name=name, discovery_base=discovery_base,
                    command_topic=command_topic, availability_topic=availability,
                    status_topic=status, status_online_payload=status_payload,
                    discovery_retain=retain == 'true')
    except ValueError as error:
        print(f'Home Assistant discovery disabled: {error}')
        return None


def publish_home_assistant_message(client, topic, payload, retain):
    """Queue HA metadata without blocking callbacks or stopping command listening."""
    try:
        result = client.publish(topic, payload=payload, qos=1, retain=retain)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f'Home Assistant publication could not be queued on {topic}: {result.rc}')
    except Exception as error:
        print(f'Home Assistant publication failed on {topic}: {error}')


def publish_home_assistant_discovery(client, userdata):
    """Expose each usable mapping as a button on one device, then mark it online."""
    ha = userdata.get('home_assistant')
    if not ha:
        return
    device = dict(identifiers=[ha['device_id']], name=ha['device_name'],
                  manufacturer='MQTT Listener with Command Execution',
                  model='MQTT Command Listener', sw_version=VERSION)
    for name, command in userdata['commands'].items():
        if not name or not command:
            continue
        # Hash the full, exact name: punctuation, Unicode and repeated spaces
        # remain distinct, while changing only the shell command preserves IDs.
        button_id = hashlib.sha256(name.encode('utf-8')).hexdigest()
        payload = dict(name=name, unique_id=ha['device_id'] + '_' + button_id,
                       command_topic=ha['command_topic'], payload_press=name,
                       retain=False, qos=0, availability_topic=ha['availability_topic'],
                       payload_available='online', payload_not_available='offline', device=device)
        publish_home_assistant_message(client, ha['discovery_base'] + button_id + '/config',
                                       json.dumps(payload, ensure_ascii=False), ha['discovery_retain'])
    publish_home_assistant_message(client, ha['availability_topic'], 'online', True)


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

    ha = userdata.get('home_assistant')
    if rc == 0 and ha:
        try:
            result, _ = client.subscribe(ha['status_topic'], qos=1)
            if result != mqtt.MQTT_ERR_SUCCESS:
                print(f'Home Assistant birth subscription could not be queued: {result}')
        except Exception as error:
            print(f'Home Assistant birth subscription failed: {error}')
        publish_home_assistant_discovery(client, userdata)


def on_message(client, userdata, msg):
    # MQTT 3 does not identify the publisher. Reserve this exact topic so a
    # wildcard subscription cannot turn our own announcement into a command.
    if userdata.get('online_topic') and msg.topic == userdata['online_topic']:
        return

    ha = userdata.get('home_assistant')
    if ha:
        # Metadata received through a wildcard command subscription must never
        # select a shell command. Compare birth bytes before ordinary decoding.
        if msg.topic == ha['status_topic']:
            if msg.payload == ha['status_online_payload'].encode('utf-8'):
                publish_home_assistant_discovery(client, userdata)
            return
        if msg.topic == ha['availability_topic'] or msg.topic.startswith(ha['discovery_base']):
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
    parser = argparse.ArgumentParser(
        description='MQTT Listener with Command Execution',
        epilog='Only exact configured payloads select commands. Matching commands run '
               'in the background through the shell as the listener account. '
               'Retained and repeated messages can run commands again.')
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION,
                        help='Show the application version and exit without reading config or connecting')
    parser.add_argument('-c', '--config', required=True,
                        help='Path to the custom text configuration file (required to listen; '
                             'no default; relative paths use the current working directory)')
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
    home_assistant = get_home_assistant_config(config, topics, online_topic)
    if home_assistant:
        userdata['home_assistant'] = home_assistant
    client = mqtt.Client(userdata=userdata)
    client.on_connect = on_connect
    client.on_message = on_message

    if home_assistant:
        # Separate from the original non-retained connection announcement.
        client.will_set(home_assistant['availability_topic'], payload='offline', qos=1, retain=True)

    if username and password:
        client.username_pw_set(username, password)

    client.connect(hostname, port, 60)
    client.loop_forever()
