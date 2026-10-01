# Versioning and changes

Every created release increments by exactly `0.0.1`. The patch component ranges from 0 to 99: `0.0.98` -> `0.0.99` -> `0.1.0`. Never create `0.0.100`. The initial unversioned source was assigned `0.0.1`; the current release builds directly on the packaged `0.0.9` baseline and is `0.0.10`. `VERSION` is the single runtime version source and is exposed by `--version`. This file is the project’s canonical change log.

## 0.0.10 — 2026-10-01

- Inspected the complete packaged 0.0.9 project before editing and ran its 52-test offline suite successfully. The reported Home Assistant issue was confirmed in the discovery refresh path: `on_connect()` publishes discovery immediately after subscribing to the HA birth/status topic, while `on_message()` previously treated a retained broker replay of the same `online` birth payload as a second fresh birth and republished the full snapshot.
- Fixed only that HA metadata path: retained messages on the configured HA birth/status topic are still reserved and ignored for command execution, but now they also do **not** trigger rediscovery. A matching **non-retained** birth message still republishes discovery, preserving recovery after a genuine later HA restart/birth. Ordinary command topics keep their existing retained/repeated-message behavior.
- Updated the existing HA regression test to prove both sides of the contract: retained `online` causes zero discovery publishes and no shell launch; fresh non-retained default/custom birth payloads still republish discovery and never execute commands. The overall test count remains 52 because the existing birth test was strengthened rather than duplicated.
- Updated `README.md`, `commands-example.txt`, and `commented_code_map.md` to describe the retained-replay guard and distinguish it from normal command-message handling. No configuration key, dependency, service directive, helper script, command mapping, discovery topic, entity ID algorithm, button QoS/retain behavior, or CLI flag changed.
- Incremented `VERSION` exactly once from `0.0.9` to `0.0.10`, refreshed `VERIFICATION.md`, and regenerated `manifest.sha256`. The final package preserves every 0.0.9 path and adds or removes no project files.

## 0.0.9 — 2026-10-01

- Inspected all 20 files in the uploaded 0.0.8 ZIP before editing and ran its complete 52-test offline suite successfully. Reviewed the listener, service, build spec, configuration example, four shell helpers, all tests, README, code map, verification report, version history, and checksum manifest as one baseline.
- Found and corrected a release-provenance inconsistency: the uploaded `manifest.sha256` referenced `previous-release-manifest.json` and `uploaded-release-manifest.json`, but neither file was present in the ZIP. The uploaded verification text also described archive counts/files that did not match the supplied 0.0.8 archive. No missing historical file was fabricated.
- Added `uploaded-release-manifest.json`, generated directly from the supplied 0.0.8 ZIP. It records the exact 20-file input inventory, sizes, SHA-256 hashes, ZIP permission fields, source-archive SHA-256, and the two stale manifest references that were absent from the upload.
- Preserved runtime behavior: `mqtt-listener.py`, `mqtt-listener.service`, `mqtt-listener.spec`, both requirements files, `commands-example.txt`, all four power helpers, and all three test modules are unchanged from the uploaded 0.0.8 baseline. Existing shell execution, retained/repeated-message behavior, MQTT subscriptions, Home Assistant discovery, Last Will, and helper safety limitations are therefore unchanged.
- Confirmed the existing CLI already exposes `-h`/`--help`, `--version`, and required `-c`/`--config` with descriptive help. Confirmed the configuration example already includes every supported listener and Home Assistant setting, so no new runtime option or duplicate parser was added.
- Updated README current-use verification commands, the full commented code map, this change log, and `VERIFICATION.md`. The supplied disclaimer/liability text remains in README with project-local links and no unrelated project name. Regenerated `manifest.sha256` so it references only files actually included in 0.0.9.
- Incremented `VERSION` exactly once from `0.0.8` to `0.0.9`. The final package preserves all 20 original project paths, adds only the actual-upload provenance manifest, excludes bytecode/build/temp caches, and is verified against both staging and the uploaded archive inventory.

## 0.0.8 — 2026-09-28

- Added optional Home Assistant MQTT button discovery using Homelab-Panel 0.0.14's per-button discovery, common device metadata, retained definitions, availability Last Will, and HA birth rediscovery pattern. The integration uses the existing MQTT client and broker credentials.
- Added nine HA settings after the MQTT settings in `commands-example.txt`: `ha_enabled` (false by default), `ha_device_id`, `ha_device_name`, `ha_discovery_prefix`, `ha_command_topic`, `ha_availability_topic`, `ha_status_topic`, `ha_status_online_payload`, and `ha_discovery_retain`. Every usable command mapping becomes a button named with the exact trimmed text before `=`. HA presses send that exact name to the existing command dispatcher, never the shell text.
- Added `valid_publish_topic`, `get_home_assistant_config`, `publish_home_assistant_message`, and `publish_home_assistant_discovery`. The original online-topic check reuses the shared topic validator with equivalent rules. Paho's existing topic matcher validates command-topic subscription coverage without adding another command subscription.
- Extended successful-connect callbacks to subscribe to HA birth messages, publish discovery, and mark availability online. Added a separate retained offline Last Will before connection. Discovery publication/subscription errors are logged without stopping command listening.
- Extended incoming-message guards to reserve HA birth, availability and this device's discovery namespace when enabled, including wildcard subscriptions. Invalid HA settings disable only HA. Existing whole-payload matching, shell execution, command retention/repetition handling, original non-retained online announcement, service and power helpers remain intact.
- Stable entity IDs combine the configured listener ID with SHA-256 of the command name; button presses are non-retained at QoS 0. Discovery/availability use QoS 1. Empty names or empty shell commands are not advertised. Removed/renamed retained definitions require manual cleanup, documented in README as with Homelab-Panel's approach.
- Added 17 offline HA tests and extended the original config-example test to cover all options, order and disabled default. Extended the inert MQTT test double with conservative topic matching. All 52 offline tests pass. A temporary localhost Mosquitto/Paho test verifies discovery, retained definitions, HA birth replay, wildcard-only command routing, harmless command dispatch, reconnect and Last Will.
- Updated current README, full code map and verification report. Preserved disclaimers and historical log entries. Added a precise 0.0.7 baseline manifest while retaining the original-upload manifest. Incremented version once to 0.0.8 and regenerated release checksums. No new runtime dependency or CLI flag was needed; `--help` and `--version` remain supported.

## 0.0.7 — 2026-09-28

- Inspected all 19 files actually supplied in the 0.0.6 ZIP and ran its 34 offline tests before editing.
- Added `--version`, which prints the program name and the release number from the adjacent `VERSION` file and exits without reading command config or creating an MQTT client. Expanded `--config` help and the help epilog to explain paths, shell execution, and retained/repeated delivery. Paho remains required for all CLI invocations.
- Added `VERSION` to the existing PyInstaller spec's data list for standalone version reporting. No duplicate runtime version constant or new command parser was introduced.
- Added one CLI regression test for version output and side-effect avoidance; extended help coverage and removed `--version` from the unsupported-argument cases. All 35 offline tests pass.
- Updated current README and full code map for flags, version resource, and actual supplied files. Preserved both disclaimers with the user's wording. Verified the unchanged config example covers all seven settings/sections and four original helper mappings.
- Added `uploaded-release-manifest.json` recording this exact input archive, all original files and hashes, its checksum text, and the four referenced but absent paths. The upload contains no `.gitigore`, `original-manifest.json`, `previous-release-manifest.json`, or `uploaded-release-manifest.json`; historical entries below describe earlier releases and do not prove those files were supplied. No missing historical contents were invented.
- Incremented `VERSION` from `0.0.6` to `0.0.7`; refreshed verification notes and checksums. Preserved every supplied file path, all four runtime functions, the service, shell helpers, dependency pins, config example, and original script permissions. Packaged all source files without caches or temporary files; see `VERIFICATION.md` for checks and limits.

## 0.0.6 — 2026-09-26

- Changed the deployment directory to `/root/Source/mqtt-listener-and-code-executer/` in the service working directory, listener script path, config path, README, and code map.
- Updated all four active helper paths in `commands-example.txt` and the existing configuration-example test to `/root/Source/mqtt-listener-and-code-executer/scripts/`. The helpers remain under the project-root `scripts/` directory.
- Incremented `VERSION` from `0.0.5` to `0.0.6`; refreshed the verification report and release checksums. Retained historical release entries unchanged.
- Listener code, helper contents, executable permissions, other service directives, all original files, and both disclaimers remain intact. Verified the requested paths, archive preservation and checksums, compilation, Bash syntax, direct CLI execution, and all 34 offline tests. Live Linux systemd operation remains untested.

## 0.0.5 — 2026-09-26

- Updated `mqtt-listener.service`: `WorkingDirectory=/root/Source/MQTT-command-executioner/` and `ExecStart=/usr/bin/python3 -u /root/Source/MQTT-command-executioner/mqtt-listener.py -c /root/Source/MQTT-command-executioner/commands.txt`.
- Preserved the Python interpreter choice, placeholder service account, startup ordering, 60-second delay, timeout, and restart policy. README explains replacing the account and selecting the virtual-environment interpreter when needed.
- Retained version 0.0.4's `scripts/` layout and complete config examples. Updated current README, code map, verification report, and checksums for the service paths. All application, helper, and test code is unchanged from 0.0.4.
- Incremented the already-created 0.0.4 package to 0.0.5. Verified the exact service paths, unchanged remaining service directives, final archive contents and permissions, compilation, CLI, Bash syntax, and all 34 offline tests. Live Linux systemd testing is still required.

## 0.0.4 — 2026-09-26

- Moved `reboot-delay.sh`, `reboot-cancel.sh`, `shutdown-delay.sh`, and `shutdown-cancel.sh` from the project root into its `scripts/` directory as requested. Their bytes and executable mode `0755` are unchanged; the old root copies are replaced by these relocated files.
- Updated all four active helper mappings in the existing `commands-example.txt` to `/root/Source/MQTT-command-executioner/scripts/`. Kept the supplied example filename, payload names, broker options, and commented optional mappings.
- Updated README installation, CLI, service-adaptation, and permission examples to use `/root/Source/MQTT-command-executioner`, and documented access through `/root`. Updated the code map for the helper locations. Both disclaimers remain unchanged.
- Updated the existing configuration-example test to check the deployment prefix and files under `scripts/`. Listener code, safety behavior, helper content, service file, dependency pins, and build recipe remain unchanged.
- Incremented `VERSION` from `0.0.3` to `0.0.4`, refreshed verification notes and checksums, and compared the final ZIP with version `0.0.3` and the original upload, accounting for the four requested relocations. All 34 offline tests pass; see `VERIFICATION.md` for checks and limitations.

## 0.0.3 — 2026-09-26

- Inspected all 22 files in the uploaded archive before editing. Preserved every path, including both ignore files, the service, helpers, build recipe, requirements, and historical manifests.
- Set `mqtt-listener.py` to Unix mode `0755` and recorded that permission in the ZIP. Kept its existing `#!/usr/bin/env python3` header; documented direct execution, virtual-environment selection, and permission restoration after extraction.
- Confirmed that the uploaded parser already accepts spaces in both payload names and commands, including `docker start open-webui = docker start open-webui`. Kept exact whole-payload lookup and `Popen(command, shell=True)` behavior. Moved mapping parsing ahead of section-header detection so a shell command ending in `:` no longer becomes a section header or prevents following mappings from being read. Added comments explaining complete strings and configured-command-only execution.
- Added five regression tests for whole multiword mappings, indentation, exact matching/rejection, quoted arguments, embedded equals signs, trailing colons, subsequent mappings, main-block wiring, and status-topic isolation. Adjusted one existing help assertion for argparse versions that do not repeat the metavar for aliases; application flags are unchanged. All 34 tests pass.
- Updated README for current behavior and every application flag, complete-payload publisher usage, Docker requirements, quoting, permissions, and existing ignore-file limitations. Preserved both existing disclaimers verbatim. Extended the complete config example with commented optional Docker/quoting examples without enabling new commands.
- Updated the full code map and replaced current verification notes with checks actually performed for this release. Added `uploaded-release-manifest.json` containing the actual uploaded archive inventory, hashes, sizes, and ZIP mode fields; retained both older JSON manifests unchanged. Regenerated `manifest.sha256` including `.gitignore`, which the uploaded checksum file omitted.
- Incremented `VERSION` exactly once from `0.0.2` to `0.0.3`. Packaged the complete source project without caches, dependencies, temporary files, or build output. See `VERIFICATION.md` for preservation totals and test limitations.

## 0.0.2 — 2026-09-25

- Added optional `online_topic`. The existing client queues plain `online` at QoS 1 without retention after each successful connection/reconnection. Publish failures are logged without terminating command listening; legacy config without this option does not publish anything.
- Reserved the exact status topic before incoming payload decoding/command lookup to prevent self-triggering with wildcard subscriptions. Existing command names, command handling on other topics, connection fields, subscriptions, and authentication remain unchanged. Invalid status topics or exact command-topic collisions disable only the new feature.
- Changed example command indentation to one literal tab. Kept all prior broker settings, command-topic values, and mapping values unchanged; the existing parser accepts both tabs and spaces.
- Added pinned `requirements.txt`, `requirements-build.txt`, and `mqtt-listener.spec` for a one-file console executable containing Python and Paho modules, with unbuffered logs. Config and external command scripts remain editable external files. The original service and power helpers are byte-identical.
- Updated current-use README with the new option, GUI-based Home Assistant trigger instructions, every build command/flag, and availability limitations. Updated the full code map and tests. Added `previous-release-manifest.json`; retained the original archive manifest and regenerated release checksums.
- Verification results, real dependency/build checks, and limits are documented in `VERIFICATION.md`.

## 0.0.1 — 2026-09-25

- Inspected all nine original files before edits; recorded their sizes and SHA-256 hashes in `original-manifest.json`.
- No application code or runtime behavior changed. Preserved `mqtt-listener.py`, `mqtt-listener.service`, all four power helpers, and `.gitigore` byte-for-byte.
- Rewrote `README.md` for current usage, both CLI flags, every config option, service management, publisher usage, and actual behavior/limits. Added the supplied disclaimer immediately after the title, preserving its wording and replacing unrelated project links with local section links. Release history remains in this file.
- Updated `commands-example.txt` with every supported option, comments, a generic device topic, and `/opt/mqtt-listener` example paths. Retained the four original payload names and corresponding helpers. Adapt paths and broker credentials before use.
- Added `commented_code_map.md` explaining every function, main-block operation, helper command, service directive, and support file.
- Added `VERSION`, offline tests in `tests/test_listener.py`, `VERIFICATION.md`, and `manifest.sha256`. The release SHA-256 manifest excludes only itself.
- Verified source compilation, offline config/callback/CLI behavior, preservation, and the extracted ZIP against the staged release and original manifest. Check details and unavailable live checks are in `VERIFICATION.md`.

Historical preservation statements above refer to those earlier releases. The supplied 0.0.6 archive contains `.gitignore` only. Cancellation behavior, shell execution, retained-message handling, the service startup delay, and payload names remain unchanged in 0.0.7.
