# MQTT Listener with Command Execution

A small Python daemon that connects to an MQTT broker, subscribes to one or more topics, and runs a predefined shell command when it receives a matching payload.

It’s useful for simple “remote control” actions (shutdown, reboot, start scripts, etc.) triggered by MQTT messages (for example from Home Assistant automations).

---

## ⚠️ Disclaimer & Responsibility

**This software is provided “as is”, without any warranty of any kind.**

By using this script, **you accept full responsibility for:**

- How the code is used  
- What commands are executed  
- Testing the script in your own environment  
- Verifying that it behaves exactly as you expect  
- Any damage, data loss, downtime, or security issues caused directly or indirectly by its use  

The author **is not liable** for:

- System damage  
- Data loss  
- Accidental shutdowns or reboots  
- Security breaches  
- Misconfiguration or misuse  

You **must** review, test, and validate the script and all configured commands before using it in production or on critical systems.

---

## What it does

- Reads a simple config file (`hostname`, `port`, `username`, `password`, `topics`, and a `commands:` section)
- Connects to an MQTT broker using `paho-mqtt`
- Subscribes to one or more MQTT topics
- When a message arrives:
  - decodes the payload as text
  - looks up a command by **exact payload match**
  - if found, runs the command using `subprocess.Popen(..., shell=True)` **in the background**

---

## Requirements

- Python 3
- `paho-mqtt`

Install dependency:

```bash
python3 -m pip install --user paho-mqtt
```

System-wide (optional):

```bash
sudo python3 -m pip install paho-mqtt
```

---

## Files

Example directory layout:

```
/root/scripts/mqtt-listener/
├── mqtt-listener.py
├── commands.txt
├── shutdown-delay.sh
├── shutdown-cancel.sh
├── reboot-delay.sh
└── reboot-cancel.sh
```

---

## Configuration file format

The config is a simple `key: value` format, plus a `commands:` section containing `payload = command` mappings.

### Example config (`commands.txt`)

```yaml
hostname: localhost
port: 1883
username: myusername
password: mypassword
topics: homeassistant/jonsbo-n3-cwwk-n355

commands:
    shutdown_delay = /root/scripts/mqtt-listener/shutdown-delay.sh
    shutdown_cancel = /root/scripts/mqtt-listener/shutdown-cancel.sh
    reboot_delay = /root/scripts/mqtt-listener/reboot-delay.sh
    reboot_cancel = /root/scripts/mqtt-listener/reboot-cancel.sh
```

### Notes

- `topics` can be a **comma-separated list**
- Payload matching is **exact**
- Commands are executed with `shell=True`
- Only map commands you **fully trust and understand**

---

## Usage

Run manually:

```bash
python3 /root/scripts/mqtt-listener/mqtt-listener.py -c /root/scripts/mqtt-listener/commands.txt
```

---

## systemd service

Create a unit file:

```ini
[Unit]
Description=MQTT Client Script
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/root/scripts/mqtt-listener/
ExecStart=/usr/bin/python3 -u /root/scripts/mqtt-listener/mqtt-listener.py -c /root/scripts/mqtt-listener/commands.txt
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mqtt-listener.service
```

---

## Testing

```bash
mosquitto_pub -h localhost -p 1883 -u myusername -P mypassword \
  -t homeassistant/jonsbo-n3-cwwk-n355 \
  -m shutdown_delay
```

---

## Security recommendations

- Secure your MQTT broker (auth + ACLs at minimum)
- Restrict who can publish to the subscribed topic(s)
- Avoid wildcards unless absolutely necessary
- Prefer dedicated scripts instead of inline shell commands
- Consider running as a restricted user with limited permissions

---

## License

No license is implied unless you add one.
