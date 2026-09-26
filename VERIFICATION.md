# Release verification — 0.0.6

## Changes and preservation

This release increments `0.0.5` to `0.0.6`. It retains the four helpers under `scripts/` and their configured `/root/Source/mqtt-listener-and-code-executer/scripts/` paths. The service now uses `/root/Source/mqtt-listener-and-code-executer/` as `WorkingDirectory`, `/root/Source/mqtt-listener-and-code-executer/mqtt-listener.py` as its script, and `/root/Source/mqtt-listener-and-code-executer/commands.txt` as its config.

The final archive contains 23 files. All version 0.0.5 paths remain. Fourteen files are byte-identical to 0.0.5; nine have intentional changes: README, VERSION, VERSIONING.md, commented_code_map.md, mqtt-listener.service, commands-example.txt, tests/test_listener.py, VERIFICATION.md, and manifest.sha256. The four helpers retain their content and executable permissions.

The uploaded archive's 22 files are also all accounted for, with those same four relocations. The extra file is the previously added uploaded-release-manifest.json. Historical manifests retain their original paths and hashes; for current preservation checks, map their four root-level helper paths to `scripts/<filename>`.

## Passed checks

- All 34 offline tests pass from the final extracted ZIP, including complete multiword command matching, exact-match rejection, parser edge cases, and online-topic isolation.
- The existing example test verifies all seven configuration settings/sections, all four original power payloads, the exact `/root/Source/mqtt-listener-and-code-executer/scripts` prefix, and the packaged helper files under `scripts/`.
- All Python files and the PyInstaller spec compile in memory. All four relocated helpers pass Bash syntax checks without executing any power operations.
- Direct execution of the extracted listener passes `--help` and `-h` with exit 0. Missing config, missing config value, and an unsupported argument exit 2. These CLI checks use real installed Paho.
- Listener source and all helper contents match version 0.0.5 byte-for-byte. The status safeguards, parser fix, exact command lookup, shell execution, and startup behavior are unchanged.
- The exact service working directory and script/config paths match the requested destination. All other service directives match version 0.0.5.
- README local links resolve and both disclaimers are unchanged. Documentation and permission commands use the new helper locations.
- ZIP contents match staged files and independently extracted files. Unix mode `0755` is retained for the listener and four helpers; other files use `0644`.
- The regenerated manifest verifies all 22 other files, including the helpers at their new locations. A checksum for the complete ZIP accompanies the archive.
- No caches, bytecode, build output, dependencies, temporary files, or deployment credentials are packaged.

## Environment and limitations

Checks used macOS 15.8, Python 3.9.6, and Paho MQTT 2.1.0. Actual MQTT/Home Assistant delivery, Docker operations, Linux systemd startup, shutdown/reboot, cancellation, and access to the requested path on your host remain untested. No PyInstaller build was repeated. No power helper was executed.

The supplied service paths are updated. Replace its placeholder account and, if using a virtual environment, select its Python interpreter using README before installation. The listener account needs access to `/root/Source/mqtt-listener-and-code-executer` when using these paths.

## Reproduce checks

From the extracted project root:

```bash
python3 -B -m unittest discover -s tests -v
sha256sum -c manifest.sha256
```

`-B` suppresses bytecode; `-m unittest` runs the test runner; `discover -s tests` selects the test folder; `-v` prints individual results. `sha256sum -c` verifies listed file hashes. On macOS use `shasum -a 256 -c manifest.sha256` instead. Checksums compare content with the supplied list, not publisher identity.

After installing the README's runtime dependencies and activating the environment, `./mqtt-listener.py --help` checks direct execution. The README includes the permission-restoration command if your extraction tool drops Unix modes.
