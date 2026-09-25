# Release verification — 0.0.2

## Scope and environment

Incremental release from 0.0.1, preserving all files from that version and the original nine-file ZIP. Verification used Windows 10 x64, Python 3.12.14, Paho MQTT 2.1.0, and PyInstaller 6.22.3. No production broker, Home Assistant instance, systemd service, shutdown command, or reboot command was used.

## Passed checks

- Compiled all packaged Python files and the PyInstaller spec in memory without distributing bytecode.
- All 29 offline tests passed from the staged project and again from the extracted final ZIP. The original tests remain, with the example-option assertion extended for `online_topic`.
- Checked successful/refused connections, reconnect announcements, exact `online` payload, QoS 1/non-retained parameters, disabled/invalid/colliding status topics, nonfatal publish failures, self-message isolation before decoding, existing commands named `online`, and tab/space equivalence.
- Real Paho source CLI: `--help` passed; missing `--config` exited 2. Existing legacy callback API produces a deprecation warning with Paho 2.1.0, but worked in the tests. It is deliberately preserved and the compatible dependency is pinned.
- Built the supplied one-file spec into a Windows x64 executable using the real PyInstaller and Paho packages. Its CLI checks passed without an external `PYTHONPATH` dependency directory. The spec collects the Paho MQTT package and embeds the Python runtime.
- Ran the real source script and built executable against a local TCP MQTT 3.1.1 protocol fixture bound to `127.0.0.1`. For both, inspected CONNECT credentials, the unchanged wildcard SUBSCRIBE, and the transmitted status PUBLISH packet after initial connection and reconnection: exact topic `device/status`, payload `online`, QoS 1, retain false.
- Echoed status back over that wildcard subscription: no command was executed. Published the same `online` payload on the original command topic: one harmless `echo COMMAND_OK` command executed. Unknown payloads were ignored. No power helper was invoked. This fixture is not a full production MQTT broker or Home Assistant test.
- Windows sandbox permissions initially blocked executable extraction of `VCRUNTIME140.dll`. The executable passed outside that restriction. Test-owned parent/child processes were terminated after verification. No workstation service was installed.
- Original archive preservation: all 9 files remain; 6 byte-identical. The listener, README, and example config are the only changed original files. The service, all four power helpers, and `.gitigore` remain byte-identical.
- Previous release preservation: all 16 version-0.0.1 files remain. The new example parses to identical hostname, port, username, password, topics, and command mappings after removing the added `online_topic`. Each example mapping has one literal leading tab. AST comparisons confirm the config parser and original command callback body after its new early-return guard are unchanged.
- Final ZIP has 21 files under one release root. Every staged file matches the ZIP and extracted copy byte-for-byte. All 20 non-manifest files match `manifest.sha256`; the manifest excludes itself. Checked original and previous-release manifests for missing files and unintended changes.
- No bytecode, cache/build directories, temporary files, installed dependencies, executable build output, local deployment config, or real credentials are in the source ZIP. Examples use placeholders. All functions are covered by the code map; README local file references resolve within the project.

The source archive includes the build recipe and requirements, not a platform-specific executable. This keeps the release suitable for rebuilding on the actual Linux host.

## Remaining limits

- The actual MQTT broker, its ACL/authentication configuration, Home Assistant automation, and service startup order have not been tested. The local fixture checks the wire protocol and behavior, not production delivery.
- The connection announcement is not retained and does not include Last Will/offline/heartbeat behavior. HA must already be listening. Queuing a publish is not proof that HA handled it. QoS 1 may redeliver messages.
- A Linux executable was not built here. Build with the included spec on the target OS/architecture (and a compatible Linux runtime). Linux systemd, helper permissions, power operations, and cancellation behavior remain untested and unchanged.
- Shell syntax checking in the previous release was blocked because the bundled Git shell could not start (`couldn't create signal pipe, Win32 error 5`). No shell files changed and no new shell test pass is claimed.
- PyInstaller reports optional platform-dependent imports and optional Paho proxy/DNS-SRV modules (`socks`, `dns`) absent from this environment. Those features are not configured or used by this application. The real direct TCP connection/reconnection path passed in the executable.

## Reproduce checks

From the extracted release root:

```bash
python3 -B -m unittest discover -s tests -v
sha256sum -c manifest.sha256
```

`-B` avoids bytecode files; `-m unittest discover -s tests -v` discovers and runs the offline tests verbosely. `sha256sum -c` compares listed file hashes; it does not authenticate the manifest. The original and previous-release manifests separately record preservation baselines. A ZIP SHA-256 file is supplied alongside the release.

Follow README.md to install runtime/build requirements, build with PyInstaller, test a harmless command, and configure a Home Assistant MQTT trigger using the selected status topic and payload `online`.
