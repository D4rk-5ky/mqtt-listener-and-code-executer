# Release verification — 0.0.14

## Scope and preservation

The baseline for this release is the supplied packaged version 0.0.13 ZIP. The complete 52-test offline suite passed before the 0.0.14 edits.

Version 0.0.14 changes only the PyInstaller deployable name/build-output contract plus version/release documentation. Runtime listener source (`mqtt-listener.py`), MQTT command handling, Home Assistant discovery, service behavior, configuration example, pinned runtime requirements, power helpers, and tests remain unchanged. The PyInstaller spec changes only its output executable name to `SnapBeforeWatchTower`.

The final build contract is intentionally strict:

```text
dist/
├── SnapBeforeWatchTower
└── README.md
```

`dist/` is recreated empty before each build. PyInstaller creates the standalone `SnapBeforeWatchTower` executable there, then `build-pyinstaller.sh` creates the deployable `README.md`. The wrapper accepts the build only when those are the only two top-level entries. Any third file or directory causes a nonzero failure.

Generated build state does not live in `dist/`. The reusable builder environment is `.pyinstaller-build/venv/` and PyInstaller work files are `.pyinstaller-build/work/`. `.pyinstaller-build/` and `dist/` are gitignored. Legacy `.build-venv/` and `build/` paths remain gitignored only to prevent stale older-release output from being committed accidentally.

The generated `dist/README.md` explains:

- `dist/` is where the PyInstaller build puts the standalone executable.
- The expected output is `dist/SnapBeforeWatchTower`.
- You create it by running `./build-pyinstaller.sh`.
- Generated binaries should not be confused with the source files.

The PyInstaller deployable is intentionally named `SnapBeforeWatchTower` to match the requested build-output contract. The source entry point remains `mqtt-listener.py`.

## Checks performed

- Baseline 0.0.13 before edits: all 52 existing offline unit tests passed.
- Final staged 0.0.14 project: all 52 offline unit tests pass.
- Python source/tests and `mqtt-listener.spec` compile with Python's built-in `compile()`.
- `build-pyinstaller.sh` and all runtime shell helpers pass `bash -n`.
- Source CLI `--version`/`--help` are checked using the same inert Paho-stub approach as prior releases; no broker is contacted.
- A controlled PyInstaller-wrapper simulation verifies that a successful build leaves exactly `dist/SnapBeforeWatchTower` and `dist/README.md`, with all work state under `.pyinstaller-build/`.
- A controlled failure simulation deliberately creates an extra `dist/` entry and confirms the wrapper rejects it.
- The final source package is scanned to exclude generated `.pyinstaller-build/`, `dist/`, `__pycache__`, `.pyc`, `.pyo`, editor backup/swap files, and temporary verification artifacts.
- `manifest.sha256` is regenerated after all source edits and verified.
- The final ZIP is extracted independently, CRC-checked, and the extracted source tests are rerun.

## Real PyInstaller limitation

This environment does not have usable package-network/DNS access and does not already contain the pinned PyInstaller/Paho build dependencies, so a real frozen executable cannot be assembled here. The wrapper's layout/invariant logic is exercised with controlled success/failure simulations instead. A normal build host with package access (or a pre-populated compatible build environment) should run:

```bash
./build-pyinstaller.sh
find dist -mindepth 1 -maxdepth 1 -printf '%f\n'
./dist/SnapBeforeWatchTower --version
./dist/SnapBeforeWatchTower --help
```

A successful build must list exactly:

```text
SnapBeforeWatchTower
README.md
```

No live MQTT broker/Home Assistant connection, systemd installation, shutdown/reboot operation, Docker command, broker ACL/credential test, or real frozen executable run was performed in this environment.
