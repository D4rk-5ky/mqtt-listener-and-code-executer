# Versioning and changes

Every created release increments by exactly `0.0.1`. The patch component ranges from 0 to 99: `0.0.98` -> `0.0.99` -> `0.1.0`. Never create `0.0.100`. The supplied source has no declared version, so this release starts at `0.0.1` from an unversioned baseline. `VERSION` records the package version; the application has no version CLI flag.

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
