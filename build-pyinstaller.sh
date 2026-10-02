#!/bin/bash
set -euo pipefail

# Build a self-contained PyInstaller onedir bundle in dist/mqtt-listener/.
# Run this script from anywhere; it always operates on the project containing it.
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BUILD_VENV="$PROJECT_DIR/.build-venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$PROJECT_DIR"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    printf 'Error: Python interpreter not found: %s\n' "$PYTHON_BIN" >&2
    exit 1
fi

printf 'Creating/reusing build environment: %s\n' "$BUILD_VENV"
if [ ! -x "$BUILD_VENV/bin/python" ]; then
    "$PYTHON_BIN" -m venv "$BUILD_VENV"
fi

printf 'Installing pinned runtime/build dependencies...\n'
"$BUILD_VENV/bin/python" -m pip install -r requirements-build.txt

printf 'Removing previous PyInstaller build output...\n'
rm -rf -- build dist

printf 'Building onedir bundle...\n'
"$BUILD_VENV/bin/python" -m PyInstaller --clean --noconfirm mqtt-listener.spec

EXECUTABLE="$PROJECT_DIR/dist/mqtt-listener/mqtt-listener"
if [ ! -x "$EXECUTABLE" ]; then
    printf 'Error: expected executable was not created: %s\n' "$EXECUTABLE" >&2
    exit 1
fi

printf '\nBuild complete.\n'
printf 'Bundle directory: %s\n' "$PROJECT_DIR/dist/mqtt-listener"
printf 'Executable:       %s\n' "$EXECUTABLE"
printf '\nBasic checks:\n'
"$EXECUTABLE" --version
"$EXECUTABLE" --help >/dev/null
printf 'PyInstaller bundle --help check: OK\n'
