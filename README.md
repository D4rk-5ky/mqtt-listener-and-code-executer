# MQTT Listener with Command Execution

## ⚠️ Disclaimer / Liability

<a id="disclaimer-liability"></a>

[Link to this section](#disclaimer-liability)

**Use this script at your own risk.**

The author takes **no responsibility or liability** for any data loss, service disruption, misconfiguration, service outage, missed backups, credential exposure, or other damage that may occur from using this script.

Before running it in production, you **must**:

- Read the entire source code
- Understand exactly what it does (and what it does _not_ do)
- Review and adapt it to your own environment
- Test it carefully in a non‑production setup

By using this script, **you accept full responsibility** for its effects.

⚠️ AI-assisted / vibe-coded experimental software. Use at your own risk.

## Disclaimer

[Link to this section](#disclaimer)

This project is AI-assisted / vibe-coded software created as a hobby project. It has not been professionally audited and may contain bugs, unsafe behavior, data-loss issues, security problems, or incorrect assumptions.

You are responsible for reviewing the code, testing it in a safe environment, making backups, and understanding what it does before using it on real data. The author is not responsible for damage, data loss, broken systems, security issues, or other problems caused by using this software.

----

## What the app does

The listener reads a text configuration file, connects to an MQTT broker, and subscribes to the configured topics. Incoming payloads are decoded as UTF-8 and stripped of leading/trailing whitespace. The resulting text is matched, case-sensitively, against the configured command names. A matching nonempty command starts in the background through `subprocess.Popen(command, shell=True)`.

The MQTT payload selects a configured command; it is not appended to that command. All command topics share the same command map. When enabled, the dedicated `online_topic` is reserved for status and ignored by command handling. Unknown payloads are logged and ignored. “Executed command in background” means process creation succeeded, not that the command completed successfully. The listener does not collect exit codes, publish command results, or wait for jobs to finish. An optional plain `online` announcement reports a successful MQTT connection.

This project targets Linux with Python 3 and `paho-mqtt`. Helpers require Bash and Linux shutdown/reboot utilities; the service requires systemd. See [the code map](commented_code_map.md) for every function, shell command, and service directive, and [verification notes](VERIFICATION.md) for testing limits.

## Install and choose an account

Extract the complete project into a directory accessible to the account that will run it. These examples use `/root/Source/mqtt-listener-and-code-executer`; adjust it consistently in your config and service.

```bash
cd /root/Source/mqtt-listener-and-code-executer
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp commands-example.txt commands.txt
chmod 600 commands.txt
chmod +x mqtt-listener.py scripts/shutdown-delay.sh scripts/shutdown-cancel.sh scripts/reboot-delay.sh scripts/reboot-cancel.sh
```

`cd` selects the extracted directory. Python's `-m venv .venv` creates an isolated environment, and `-m pip install -r requirements.txt` installs the pinned Paho dependency there; `-r` reads the requirements file. `cp` creates your local configuration; edit it before starting. `chmod 600` restricts config read/write access to its owner; it may contain a password. `chmod +x` makes the listener and four helpers executable. The release ZIP records mode `0755` for these five scripts; this command restores it if your extraction tool drops Unix permissions.

The four helpers are in the project-root `scripts/` folder. The example configuration uses `/root/Source/mqtt-listener-and-code-executer/scripts/` for their absolute paths. The chosen account needs access to the directory, scripts, and config, including permission to traverse `/root` when using this location. Power commands also require appropriate operating-system privileges. Commands run as the listener's account; it does not grant privileges. Restrict who can publish to its broker topics. There is no application dry-run mode.

## Configuration: all available options

This is a custom line-based format, **not YAML**. Copy [commands-example.txt](commands-example.txt), which contains all supported settings. Put broker settings before `commands:`.

| Setting | Default when absent | Meaning |
| --- | --- | --- |
| `hostname` | `localhost` | MQTT broker hostname or address. |
| `port` | `1883` | Broker port, converted with `int()`. An invalid integer stops startup. |
| `username` | None | Broker username. Authentication is configured only when both credentials are nonempty. |
| `password` | None | Plain-text broker password. If either credential is absent/empty, neither is passed to Paho. |
| `topics` | Empty string | Comma-separated topic filters, trimmed of surrounding spaces. Supply at least one nonempty filter; empty entries are not validated/removed. |
| `online_topic` | Disabled | Optional dedicated publish topic for the plain `online` announcement. Keep it separate from command topics; use a unique topic per listener. |
| `commands:` | Empty mapping | Begins `payload = shell command` mappings. The first `=` separates the fields; later `=` characters remain in the command. |

Blank lines and whole lines beginning with `#` after trimming are ignored. Inline comments are **not** supported. Keys, values, command names, and commands have surrounding whitespace stripped. Duplicate keys or command names use the last value. Unknown settings do not add capabilities. Do not quote values as if this were YAML: quote characters become part of the value.

Outside a command mapping, a line ending in `:` is interpreted as a section header, so an empty setting such as `password:` is not stored as an empty value. Omit unused credential lines entirely.

For a first test, use a dedicated broker topic and only a harmless command:

```text
hostname: localhost
port: 1883
topics: mqtt-listener/test-device/commands

commands:
	ping = /usr/bin/printf 'MQTT listener test\n'
```

Omitting credentials works only if the broker allows unauthenticated access. Add both when required. Use trusted, absolute script paths; relative command paths use the listener's working directory. No config option enables TLS, dry-run, command timeouts, completion reporting, retained-message rejection, or topic-specific command maps. Keepalive is fixed at 60 seconds; subscriptions use Paho's default QoS of 0. This configuration does not encrypt broker traffic.

## Announce online to Home Assistant

Keep your existing `hostname`, `port`, `username`, `password`, `topics`, and command mappings. Add just this setting **before** `commands:`, choosing a unique status topic for this listener:

```text
online_topic: mqtt-listener/example-device/status
```

After a successful MQTT connection (including reconnection), the listener publishes exactly `online` to this topic using the same client, broker, and credentials. It uses QoS 1 and `retain=False`; no JSON, additional status payload, or second connection is required. The broker account must have permission to publish to this status topic as well as its existing subscription permissions.

An omitted/blank setting disables announcements and preserves old config behavior. A topic containing `+`, `#`, a null character, more than 65535 UTF-8 bytes, or an exact match to a command topic disables announcements with a log message; existing command listening continues. A wildcard command subscription may include the status topic: received messages on that exact reserved topic are ignored before decoding or command lookup. MQTT 3 does not provide the original publisher identity, so this is topic isolation, not sender authentication. An `online` command on any original command topic still works.

The publish is queued without blocking the network callback. A queue error/exception is logged and does not stop command handling. The queued log is not proof Home Assistant received it. The announcement follows connection acceptance and subscription requests; it does not verify subscription acknowledgments or command readiness. QoS 1 can redeliver messages, so make HA actions safe to repeat.

In Home Assistant's automation visual editor:

1. Create or edit an automation and add an **MQTT** trigger (search for MQTT if needed).
2. Set **Topic** to the exact `online_topic`, for example `mqtt-listener/example-device/status`.
3. Set **Payload** to `online`, with no quotes, JSON, or value template.
4. Add the action you want, save/enable the automation, and then restart the listener to test it. Check the automation's traces.

This uses Home Assistant's [MQTT topic/payload trigger](https://www.home-assistant.io/docs/automation/trigger/#mqtt-trigger). HA must be connected and listening when the message arrives. Because the message is not retained, an HA restart will not replay an old “online” event. This is a connection announcement, **not continuous availability monitoring**: there is no heartbeat, Last Will, `offline` payload, MQTT discovery, or automatic availability entity.

The command example uses one literal tab before each active mapping. Spaces and tabs are both accepted as indentation.

## Commands containing spaces

Under `commands:`, the entire left side of the first `=` is the MQTT payload to match; the entire right side is the shell command to launch. Spaces inside either side are preserved. For example:

```text
commands:
    docker start open-webui = docker start open-webui
```

Publish exactly `docker start open-webui` on a configured command topic. Do not include the `=` or the right side in the MQTT message. Do not surround the payload in quote characters in an MQTT dashboard field. In a shell, quote the publisher argument so the shell passes it as one value:

```bash
mosquitto_pub -h localhost -p 1883 -t mqtt-listener/example-device/commands -m 'docker start open-webui'
```

Publisher flags: `-h` selects the broker, `-p` its port, `-t` the topic, and `-m` the complete payload. Adapt the broker/topic and authentication to your config. This example starts a real container when that mapping is enabled. Docker must be installed, the container must exist, and the listener account must have access to Docker. `docker start` starts an existing stopped container; `open-webui` is its name.

You can instead choose a short payload alias, such as `start_webui = docker start open-webui`, and publish `start_webui`. Both forms use the same exact-match lookup. Matching is case-sensitive; internal double spaces differ from single spaces. Surrounding whitespace is trimmed. Unknown, partial, or appended payloads are ignored.

Quote individual shell arguments or executable paths containing spaces on the right side, for example `run tool = "/opt/my tools/runner" --label="A B"`. Do not quote the whole right side as one executable name. Shell operators and later `=` characters are preserved. A command ending in `:` is also preserved as a mapping. The first `=` is always the delimiter, so the payload name cannot contain `=`. Only trusted configured shell text is executed; incoming text selects a mapping.

## CLI: all flags

```bash
.venv/bin/python mqtt-listener.py --help
.venv/bin/python mqtt-listener.py --config /root/Source/mqtt-listener-and-code-executer/commands.txt
```

| Flag | Value / required | Purpose and example |
| --- | --- | --- |
| `-h`, `--help` | No value; optional | Print usage and exit without reading config or connecting. Example: `mqtt-listener.py -h`. Paho must still be installed because it is imported first. |
| `-c`, `--config` | File path; required | Read this file. Example: `mqtt-listener.py -c /root/Source/mqtt-listener-and-code-executer/commands.txt`. Relative paths use the current working directory. There is no default config file. |

For direct execution, activate the virtual environment so the existing `#!/usr/bin/env python3` header selects Python with Paho installed:

```bash
. .venv/bin/activate
./mqtt-listener.py --help
./mqtt-listener.py --config /root/Source/mqtt-listener-and-code-executer/commands.txt
```

The shell's `. .venv/bin/activate` loads the environment into the current shell; `./` selects the script in the current directory. If execution is denied after extraction, restore permissions with the installation command above. A filesystem mounted with execution disabled also prevents direct execution; use the explicit interpreter commands above or an executable filesystem. Explicit `.venv/bin/python` invocation does not require activation. These are the only application flags: there is no `--version` or `--dry-run`. The package version is in [VERSION](VERSION). Python's `-u`, used in the service, makes stdout/stderr unbuffered for prompt logs; it is an interpreter flag. Missing/unknown arguments produce argparse errors. Missing/unreadable config, an invalid port, or initial connection failure can stop the application. Ctrl+C stops a foreground listener but does not reliably cancel previously launched commands.

## Test a harmless message

Start the listener with the test-only config above, then use an MQTT client such as `mosquitto_pub`:

```bash
mosquitto_pub -h localhost -p 1883 -t mqtt-listener/test-device/commands -m ping
```

Here `-h` means broker host, `-p` broker port, `-t` publish topic, and `-m` text payload. These are publisher flags, not listener flags. This example requires a local broker permitting this unauthenticated test; configure authentication in your MQTT client otherwise. Do not retain action messages. Expect a matching log entry and harmless output. There is no result acknowledgment from the listener.

## Included power helpers

| Example payload | Helper | Behavior |
| --- | --- | --- |
| `shutdown_delay` | `scripts/shutdown-delay.sh` | Starts a background subshell: wait 60 seconds, then `shutdown -P now`; records its PID in `/tmp/shutdown.pid`. |
| `shutdown_cancel` | `scripts/shutdown-cancel.sh` | If the PID file exists, attempts to kill that PID; removes the file only if killing succeeds. |
| `reboot_delay` | `scripts/reboot-delay.sh` | Starts a background subshell: wait 60 seconds, then `reboot`; records its PID in `/tmp/reboot.pid`. |
| `reboot_cancel` | `scripts/reboot-cancel.sh` | Attempts the same recorded-PID cancellation for reboot. |

Repeated starts overwrite the PID file and can leave earlier timers running. Cancellation attempts only the recorded PID; it is not verified process-tree cancellation or a guarantee against shutdown/reboot. PID files can be stale and PIDs can be reused; these scripts do not validate ownership. Test on a disposable Linux host before relying on cancellation. The code map explains every shell operation.

## systemd service

The supplied [mqtt-listener.service](mqtt-listener.service) uses `/root/Source/mqtt-listener-and-code-executer/` as its working directory, with `mqtt-listener.py` and `commands.txt` in that directory. Before installing it, replace the placeholder account and select the Python interpreter containing Paho. For the virtual environment installed above, use:

```ini
User=your_username
WorkingDirectory=/root/Source/mqtt-listener-and-code-executer/
ExecStart=/root/Source/mqtt-listener-and-code-executer/.venv/bin/python -u /root/Source/mqtt-listener-and-code-executer/mqtt-listener.py -c /root/Source/mqtt-listener-and-code-executer/commands.txt
```

Replace `your_username` with your chosen account. The packaged unit uses `/usr/bin/python3` and the requested project paths; its placeholder account must be changed to an account that can access this location. When using a virtual environment, select its Python interpreter.

The unit uses `Type=simple`, orders startup after `network.target`, sets `TimeoutStartSec=180`, runs `/bin/sleep 60` before every start, and uses `Restart=always`. `network.target` does not guarantee broker reachability. `WantedBy=multi-user.target` enables normal boot startup. See the code map for all directives.

After adapting and safely testing the unit/config:

```bash
sudo cp mqtt-listener.service /etc/systemd/system/mqtt-listener.service
sudo systemctl daemon-reload
sudo systemctl enable --now mqtt-listener.service
sudo systemctl status mqtt-listener.service
sudo journalctl -u mqtt-listener.service -f
```

`sudo cp` installs the unit with administrator privileges. `daemon-reload` makes systemd reread unit definitions. `enable --now` enables boot startup **and immediately starts** the listener. `status` displays service state. `journalctl -u` selects the unit and `-f` follows new logs until Ctrl+C.

After config changes, use `sudo systemctl restart mqtt-listener.service` (including its 60-second pre-start delay). After unit changes, run `daemon-reload` before restarting. `sudo systemctl stop mqtt-listener.service` stops it; `sudo systemctl disable mqtt-listener.service` disables future boot startup. Do not rely on stopping the listener to cancel a scheduled power operation.

## Operational limits

- Retained/repeated messages are processed normally. Reconnection/resubscription can trigger actions again. Use dedicated topics, controlled publishers, and no retained action payloads.
- Every match starts a new shell process; jobs can overlap without locking, limits, or deduplication. Configured shell text can perform any operation the account is allowed to perform.
- Invalid UTF-8 can raise from the callback. The application does not comprehensively handle connection/subscription errors.
- Config reload requires restart. Logs can include payloads and configured command text; avoid embedding secrets and restrict log access.
- `.gitignore` excludes `commands*`. Its supplied `! commands-example.txt` pattern has a space and does not correctly re-include the example; use `!commands-example.txt` in your own repository if needed. The preserved `.gitigore` is misspelled and ignored by Git. Review ignore rules for virtual environments and secrets before committing a deployment.

## Build a standalone executable with PyInstaller

Build on the target operating system and CPU architecture. For the supplied Linux systemd service and power helpers, build on compatible Linux; a Windows `.exe` cannot run that Linux service. A PyInstaller bundle contains the Python interpreter and necessary Python modules, so the target does not need a separate Python/Paho installation. See [PyInstaller's platform/build explanation](https://pyinstaller.org/en/stable/operating-mode.html).

From the project root on Linux:

```bash
python3 -m venv .build-venv
.build-venv/bin/python -m pip install -r requirements-build.txt
.build-venv/bin/python -m PyInstaller --clean --noconfirm mqtt-listener.spec
./dist/mqtt-listener --help
./dist/mqtt-listener --config /root/Source/mqtt-listener-and-code-executer/commands.txt
```

On Windows PowerShell, use the same spec:

```powershell
python -m venv .build-venv
.\.build-venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.build-venv\Scripts\python.exe -m PyInstaller --clean --noconfirm mqtt-listener.spec
.\dist\mqtt-listener.exe --help
```

`-m venv` creates the build environment; `-m pip install -r` reads the build dependencies, including the runtime requirements. `-m PyInstaller` runs the builder. `--clean` clears PyInstaller caches before building; `--noconfirm` permits replacement of build output without asking. The spec creates a single console executable named `mqtt-listener` (`.exe` on Windows), collects the entire `paho.mqtt` package, and enables unbuffered output for service logs. It intentionally does not embed credentials, command config, or your external scripts. The build generates `build/`, `dist/`, and cache files locally; those are excluded from the source release. [PyInstaller documents these options](https://pyinstaller.org/en/stable/usage.html).

Keep `commands.txt` and all scripts referenced by its command mappings on the target, at their configured paths. Bash, systemd, shutdown/reboot utilities, permissions, and other programs invoked by your commands are operating-system dependencies; PyInstaller does not supply them. A one-file executable also needs permission to extract its bundled libraries into the target's temporary directory.

To use a Linux build with the supplied service, keep its other settings and set its adapted `ExecStart` to:

```ini
ExecStart=/root/Source/mqtt-listener-and-code-executer/mqtt-listener -c /root/Source/mqtt-listener-and-code-executer/commands.txt
```

Install your built executable at that path first. The packaged service launches the Python source from `/root/Source/mqtt-listener-and-code-executer`; change `ExecStart` as shown only when using a standalone build. Do not add Python's `-u` flag to the executable; the spec already enables unbuffered output.

## Offline checks

```bash
python3 -B -m unittest discover -s tests -v
```

`-B` suppresses bytecode files. `-m unittest` invokes the test runner; `discover -s tests` selects the test directory and `-v` prints individual results. Tests mock MQTT and process launches: they never connect to a broker or execute configured commands. See [VERIFICATION.md](VERIFICATION.md) for release checks and untested deployment behavior.

## License

The original archive supplies no license file. No license is implied by this documentation.
