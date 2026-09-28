# Release verification — 0.0.8

## Scope and preservation

This release increments 0.0.7 once to 0.0.8 and adds optional Home Assistant MQTT device/button discovery using the same per-button discovery and common device metadata pattern as Homelab-Panel 0.0.14. HA settings follow the MQTT settings in `commands-example.txt` and default to disabled. Names and press payloads use the exact trimmed command names before `=`.

The ZIP contains 22 files. All 20 files from 0.0.7 remain. Eleven are byte-identical; nine are intentionally updated: README, VERIFICATION, VERSION, VERSIONING, commands-example, commented_code_map, manifest.sha256, mqtt-listener.py, and tests/test_listener.py. Added files are `tests/test_home_assistant.py` and `previous-release-manifest.json`, which records the exact 0.0.7 archive inventory and hashes.

All 19 files actually present in the original supplied 0.0.6 archive also remain. Nine are byte-identical to that upload; ten have documented changes across 0.0.7 and 0.0.8. The original-upload manifest remains byte-identical to 0.0.7 and records the input archive's four missing historical references. No missing historical contents have been invented.

The original config parser, command dispatch statements, command subscription loop, and non-retained online announcement are preserved. Online-topic validation now reuses the shared publish-topic validator with equivalent rules. The service, four helpers, dependency pins, build recipe, ignore file, and online tests are byte-identical to 0.0.7. Every original broker option and command mapping remains in the expanded config example.

## Passed checks

- The 35 baseline offline tests passed before editing. All 52 release tests pass from the independently extracted ZIP: 17 new HA tests plus the existing listener and online tests.
- HA tests cover exact names/press payloads, shared device metadata, stable/distinct IDs, disabled/legacy configs, topic validation and collision rejection, wildcard routing through Paho's matcher, Last Will wiring, reconnect callbacks, HA birth replay, metadata isolation before decoding, empty mappings, publication/subscription errors, and reuse of the existing command handler. MQTT clients and processes are mocked in these tests.
- A separate live test used a temporary Mosquitto 2.1.2 broker listening only on 127.0.0.1 with real Paho 2.1.0. It verified two discovered buttons on one device, retained discovery and availability received by a later subscriber, exact plain-name command dispatch, HA birth rediscovery, metadata isolation with a wildcard-only command subscription, reconnect after broker restart, and retained offline Last Will after listener termination.
- The live test used its own scratch configuration, ephemeral port, broker, and observers. Only a harmless `printf` command writing a scratch marker was executed; the original power mappings were never loaded or run. The temporary broker and clients were stopped afterward. HA birth and button press messages were simulated using real MQTT clients, not an actual Home Assistant server.
- All Python files and the PyInstaller spec compile in memory. All four helpers pass Bash syntax checks without execution.
- Real-Paho `--help`, `-h`, and `--version` checks exit 0, including direct executable launch and invocation outside the project directory. The version output is `mqtt-listener.py 0.0.8`. Missing config, missing config value, and unknown flags exit 2.
- The unchanged build spec includes `VERSION` as a bundled data resource when evaluated with inert builder stand-ins. All added application imports are from the Python standard library; runtime requirements are unchanged.
- The example includes all seven original settings/sections and all nine HA settings. The test verifies their placement, disabled default, original helper paths and original payloads. README local file links resolve; both disclaimers retain their wording; the code map names every application/test function and explains the commands and settings.
- Final ZIP contents, bytes and permissions match staging and independent extraction. All original paths are accounted for against both the actual uploaded archive and 0.0.7. Unix mode 0755 is retained for the listener and four helpers; other files are 0644.
- The final ZIP passes CRC verification. The release manifest checks all 21 other files; a separate checksum covers the ZIP. No bytecode, `__pycache__`, build/dependency cache, scratch tests/logs, temporary files, or deployment credentials are packaged.

## Limitations and deployment checks

Checks ran on macOS with Python 3.9.6, Paho MQTT 2.1.0, and Mosquitto 2.1.2. The existing Paho callback API emits a deprecation warning; callback compatibility is deliberately preserved.

No actual Home Assistant UI or entity registry was available, so its rendered device page, user-customized names, dashboard cards and retained-entity cleanup were not directly tested. Discovery schema and lifecycle were checked against official HA documentation and the local Homelab-Panel implementation. The local broker test confirms transport behavior but does not verify your broker credentials/ACLs, network or HA configuration.

Linux systemd startup, Docker actions, shutdown/reboot/cancellation, and a PyInstaller executable build remain untested. No service was installed. PyInstaller is not installed in this checking environment; only its recipe wiring was checked.

Renamed/removed commands can leave old retained discovery definitions. README explains explicit cleanup. Availability reports the MQTT connection, not successful command completion; repeated command messages retain the listener's original behavior.

## Reproduce offline checks

From the extracted project directory:

```bash
python3 -B -m unittest discover -s tests -v
sha256sum -c manifest.sha256
```

`-B` suppresses bytecode; `-m unittest` invokes the runner; `discover -s tests` selects tests; `-v` prints individual results. `sha256sum -c` verifies listed hashes. On macOS use `shasum -a 256 -c manifest.sha256`. Checksums validate content against the supplied list, not publisher identity.

After installing runtime dependencies:

```bash
python3 -B mqtt-listener.py --help
python3 -B mqtt-listener.py --version
```

`--help` explains all listener flags; `--version` prints its name and release. Both exit without command config or a broker connection. Paho and the adjacent VERSION file are required. README gives a harmless HA test configuration and installation steps.
