# Versioning and changes

Every created release increments by exactly `0.0.1`. The patch component ranges from 0 to 99: `0.0.98` -> `0.0.99` -> `0.1.0`. Never create `0.0.100`. The initial unversioned source was assigned `0.0.1`; the uploaded baseline for the current release is `0.0.2`, and this release is `0.0.6`. `VERSION` records the package version; the application has no version CLI flag.

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

The original `.gitigore` filename is intentionally preserved. It does not protect deployment secrets from Git; this limitation is documented. Cancellation behavior, shell execution, retained-message handling, the service startup delay, and payload names were not changed.
