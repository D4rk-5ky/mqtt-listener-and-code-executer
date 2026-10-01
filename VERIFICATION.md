# Release verification — 0.0.10

## Scope and preservation

The baseline for this release is the packaged version 0.0.9 ZIP, SHA-256 `a5597282fd85f35e251b2ea7b995db0125e656805f63120b08b85e1ea480520c`, containing 21 project files. The complete baseline 52-test offline suite passed before editing.

Version 0.0.10 makes one runtime behavior change in the Home Assistant discovery refresh path. On a successful MQTT connection, `on_connect()` already subscribes to the configured HA birth/status topic and immediately publishes the complete discovery snapshot. In 0.0.9, a retained broker replay of the configured HA `online` payload was then treated by `on_message()` as another birth and caused the same discovery snapshot to be published again. Version 0.0.10 ignores retained messages for rediscovery on that reserved HA status topic while still reserving them from command execution. A matching non-retained HA birth payload still republishes discovery.

This does **not** add a general retained-command filter. Ordinary configured command topics keep the existing behavior: retained and repeated matching command payloads can still execute commands. Button discovery still publishes no `state_topic`; button presses remain QoS 0 and non-retained. Discovery topic construction, entity IDs, availability Last Will, command matching, shell execution, service behavior, dependencies, and helper scripts are unchanged.

All 21 baseline paths are preserved and no project files are added or removed. Twelve files remain byte-identical to 0.0.9. Nine are intentionally changed: `mqtt-listener.py`, `tests/test_home_assistant.py`, `README.md`, `commands-example.txt`, `commented_code_map.md`, `VERSION`, `VERSIONING.md`, `VERIFICATION.md`, and `manifest.sha256`.

## Checks performed

- Baseline before edits: all 52 offline unit tests passed.
- Final staged project: all 52 offline unit tests pass. Tests use inert/mock MQTT clients and mocked process launches; they do not execute configured shell commands or contact a broker.
- The strengthened HA regression test reproduces the affected startup ordering: `on_connect()` publishes one discovery snapshot, then a retained `homeassistant/status=online` replay produces no additional publication and no shell execution. A later matching non-retained birth payload still republishes discovery. Custom non-retained birth payload handling remains covered.
- The existing retained/repeated-command test still passes, confirming the new filter is limited to the reserved HA birth/status metadata path rather than normal command topics.
- `mqtt-listener.py`, all three Python test modules, and `mqtt-listener.spec` compile successfully with Python's built-in in-memory `compile()`.
- All four shell helpers pass `bash -n` syntax checks without execution. Shutdown and reboot commands were not run.
- CLI parsing was exercised through the real script with a temporary inert Paho import stub: `--help`, `-h`, and `--version` exit 0; version output is `mqtt-listener.py 0.0.10`; missing required config, a missing config value, and an unknown flag exit 2. No broker connection was attempted for these checks.
- The existing configuration-example test passes and verifies the example contains every supported setting/section and the original helper mappings. The example was updated only to document the retained HA birth replay behavior; no option was added or removed.
- README local project links resolve, its current-use documentation describes the new retained-replay rule, and both supplied disclaimer/liability sections remain present.
- `manifest.sha256` verifies every final release file except itself and contains no missing path.
- The final ZIP is independently extracted and compared byte-for-byte with staging. Its file-path set is also compared with the 0.0.9 baseline: all 21 paths are preserved with no additions or deletions.
- ZIP CRC verification passes. Executable mode `0755` is recorded for `mqtt-listener.py` and the four shell helpers; regular project files are recorded as `0644`.
- The packaged tree is scanned to exclude `__pycache__`, `.pyc`, `.pyo`, build/dist output, dependency caches, editor swap/backup files, and temporary verification artifacts.

## Environment and checks not fully performed

Verification runs under Python 3.13.5. The environment does not have the pinned `paho-mqtt`, Mosquitto, or PyInstaller installed. Therefore this release does not include a live MQTT broker/Home Assistant test, a real-Paho connection/reconnect test, or an actual PyInstaller build. The regression is covered with the project's Paho test double and direct callback tests, but that is not a substitute for deployment testing with the real broker and Home Assistant UI/entity registry.

No systemd unit was installed or started. Linux shutdown, reboot, delayed cancellation, Docker actions, broker ACLs/credentials, network disconnect timing, Home Assistant UI timestamp rendering, retained discovery cleanup, and a frozen executable were not exercised. These remain deployment-specific checks. The power helper scripts retain their existing PID-file/repeated-delay limitations documented in README and the code map.

## Reproduce available checks

From the extracted project directory:

```bash
python3 -B -m unittest discover -s tests -v
sha256sum -c manifest.sha256
python3 -B mqtt-listener.py --help
python3 -B mqtt-listener.py --version
```

The first two commands work without a broker; the tests supply their own MQTT stubs. Direct `--help` and `--version` need the runtime dependency installed because Paho is imported before argument parsing. Install `requirements.txt` in the intended environment before using those direct commands. On macOS, use `shasum -a 256 -c manifest.sha256` instead of `sha256sum -c`. Checksums verify content against the release list, not publisher identity.
