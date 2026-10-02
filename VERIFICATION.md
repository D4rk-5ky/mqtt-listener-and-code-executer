# Release verification — 0.0.11

## Scope and preservation

The baseline for this release is the uploaded packaged version 0.0.10 ZIP, SHA-256 `d74dcf8b49ab9479bee5c9a14d8ccbb3d18721b8b85ce2bfaad455484d815c96`, containing 21 project files under one project-root directory. The complete baseline 52-test offline suite passed before editing.

Version 0.0.11 is a build/packaging release. The runtime listener source (`mqtt-listener.py`), command example, service unit, pinned requirements, all four power helpers, all three test modules, and the existing provenance JSON are byte-identical to the uploaded 0.0.10 baseline. MQTT subscriptions, command matching/execution, Home Assistant discovery, availability, retained-message behavior, authentication, service behavior, and helper behavior are therefore unchanged.

The existing PyInstaller spec is changed from one-file to onedir mode. It reuses the existing `collect_all('paho.mqtt')` dependency collection and `VERSION` data entry, builds the console executable with `exclude_binaries=True`, and adds a `COLLECT(...)` stage. The intended deployable result is the complete `dist/mqtt-listener/` directory containing the executable and all bundled Python/Paho/runtime libraries and support files.

One new source file is added: executable `build-pyinstaller.sh`. It creates/reuses `.build-venv`, installs the pinned `requirements-build.txt`, removes only project-root `build/` and `dist/`, invokes the shared spec with `--clean --noconfirm`, verifies `dist/mqtt-listener/mqtt-listener`, and runs bundled `--version` and `--help` smoke checks. `.gitignore` is also corrected/expanded so the config example is re-included and build/cache output is ignored.

The final source tree contains all 21 baseline paths plus `build-pyinstaller.sh`. No baseline path is removed or relocated. Eight baseline files are intentionally changed: `.gitignore`, `README.md`, `VERIFICATION.md`, `VERSION`, `VERSIONING.md`, `commented_code_map.md`, `manifest.sha256`, and `mqtt-listener.spec`. Thirteen baseline files remain byte-identical.

## Checks performed

- Baseline before edits: all 52 existing offline unit tests passed.
- Final staged project: all 52 offline unit tests pass. These tests use inert/mock MQTT clients and mocked process launches; they do not contact a broker or execute configured commands.
- `mqtt-listener.py`, all three Python test modules, and `mqtt-listener.spec` compile successfully with Python's built-in in-memory `compile()`.
- `build-pyinstaller.sh` and all four runtime shell helpers pass `bash -n` syntax checks. Shutdown/reboot commands were not executed.
- Source CLI parsing was exercised with a temporary inert Paho import stub: `--version` exits successfully and prints `mqtt-listener.py 0.0.11`; `--help` exits successfully and documents `-h/--help`, `--version`, and required `-c/--config`. Unsupported/missing argument handling exits with argparse status 2. The stub is outside the project and is not packaged.
- The existing configuration-example regression test passes and confirms `commands-example.txt` still contains every supported runtime setting/section and all four original helper mappings. No runtime configuration option was added or removed in this release.
- Baseline comparison confirms `mqtt-listener.py`, `commands-example.txt`, `requirements.txt`, `requirements-build.txt`, `mqtt-listener.service`, all four power helpers, all three test modules, and `uploaded-release-manifest.json` are unchanged from 0.0.10.
- The README retains both requested disclaimer/liability sections and documents only current application/build usage, including the onedir output layout and complete-directory deployment requirement.
- The code map explains the current listener functions, CLI/main operations, service directives, shell helpers, tests, PyInstaller spec stages, build wrapper commands, and why those operations exist.
- `manifest.sha256` is regenerated after all edits and verifies every final release file except itself.
- The packaged tree is scanned to exclude `.build-venv`, `build`, `dist`, `__pycache__`, `.pyc`, `.pyo`, editor swap/backup files, and temporary verification artifacts.
- The final ZIP is independently extracted and compared byte-for-byte with staging. Its file-path set is compared with the uploaded 0.0.10 baseline: all 21 baseline paths are preserved and the only new path is `build-pyinstaller.sh`.
- ZIP CRC verification passes. Executable mode `0755` is recorded for `mqtt-listener.py`, `build-pyinstaller.sh`, and all four runtime helpers; regular project files are recorded as `0644`.

## PyInstaller build attempt and limitation

A real `./build-pyinstaller.sh` run was attempted in the verification environment. The wrapper successfully created `.build-venv` and reached its pinned dependency installation step. The environment has no working package-network/DNS access and did not already contain `paho-mqtt` or PyInstaller, so pip could not obtain `paho-mqtt==2.1.0`; the build stopped before PyInstaller was invoked. The temporary `.build-venv`, `build/`, and `dist/` paths were removed before packaging.

Because of that environment limitation, this release could not perform an actual PyInstaller assembly or execute the produced onedir binary. The spec and wrapper were syntax/static checked, and the wrapper's dependency-install failure was correctly propagated as a nonzero exit. A deployment environment with package access (or a pre-populated build venv/wheel source) must run `./build-pyinstaller.sh` to complete the real frozen-bundle test.

No live MQTT broker/Home Assistant connection, systemd installation, shutdown/reboot operation, Docker command, broker ACL/credential test, network disconnect/reconnect test, or Windows PyInstaller build was performed. These remain deployment-specific checks.

## Reproduce available checks

From the extracted project directory:

```bash
python3 -B -m unittest discover -s tests -v
bash -n build-pyinstaller.sh scripts/*.sh
sha256sum -c manifest.sha256
python3 -B mqtt-listener.py --help
python3 -B mqtt-listener.py --version
```

The unit tests do not require a broker and supply their own MQTT stubs. Direct source `--help`/`--version` require the runtime dependency because Paho is imported before argument parsing; install `requirements.txt` first in a normal deployment environment.

To build the complete onedir bundle when dependencies are available:

```bash
./build-pyinstaller.sh
./dist/mqtt-listener/mqtt-listener --version
./dist/mqtt-listener/mqtt-listener --help
```

Keep the entire `dist/mqtt-listener/` directory together when deploying the frozen application.
