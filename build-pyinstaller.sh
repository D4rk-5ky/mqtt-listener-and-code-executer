#!/bin/bash
set -euo pipefail

# Build one self-contained PyInstaller executable and create the deployable dist/ README.
# dist/ is reserved for exactly two files: SnapBeforeWatchTower and README.md.
# All PyInstaller work state and the isolated build venv stay under .pyinstaller-build/.
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BUILD_ROOT="$PROJECT_DIR/.pyinstaller-build"
BUILD_VENV="$BUILD_ROOT/venv"
WORK_DIR="$BUILD_ROOT/work"
DIST_DIR="$PROJECT_DIR/dist"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$PROJECT_DIR"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    printf 'Error: Python interpreter not found: %s\n' "$PYTHON_BIN" >&2
    exit 1
fi

mkdir -p -- "$BUILD_ROOT"

printf 'Creating/reusing build environment: %s\n' "$BUILD_VENV"
if [ ! -x "$BUILD_VENV/bin/python" ]; then
    "$PYTHON_BIN" -m venv "$BUILD_VENV"
fi

printf 'Installing pinned runtime/build dependencies...\n'
"$BUILD_VENV/bin/python" -m pip install -r requirements-build.txt

printf 'Removing previous PyInstaller work/output...\n'
rm -rf -- "$WORK_DIR" "$DIST_DIR"
mkdir -p -- "$WORK_DIR" "$DIST_DIR"

# Refuse to build into anything except the controlled empty dist directory.
if find "$DIST_DIR" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
    printf 'Error: dist directory is not empty before build: %s\n' "$DIST_DIR" >&2
    exit 1
fi

printf 'Building one-file executable...\n'
"$BUILD_VENV/bin/python" -m PyInstaller \
    --clean \
    --noconfirm \
    --distpath "$DIST_DIR" \
    --workpath "$WORK_DIR" \
    mqtt-listener.spec

EXECUTABLE="$DIST_DIR/SnapBeforeWatchTower"
DIST_README="$DIST_DIR/README.md"

if [ ! -f "$EXECUTABLE" ] || [ ! -x "$EXECUTABLE" ]; then
    printf 'Error: expected executable was not created: %s\n' "$EXECUTABLE" >&2
    exit 1
fi

cat > "$DIST_README" <<'EOF'
# PyInstaller build output

- `dist/` is where the PyInstaller build puts the standalone executable.
- The expected output is `dist/SnapBeforeWatchTower`.
- You create it by running `./build-pyinstaller.sh`.
- Generated binaries should not be confused with the source files.
EOF

mapfile -d '' DIST_ENTRIES < <(find "$DIST_DIR" -mindepth 1 -maxdepth 1 -print0)
if [ "${#DIST_ENTRIES[@]}" -ne 2 ] || [ ! -f "$EXECUTABLE" ] || [ ! -f "$DIST_README" ]; then
    printf 'Error: dist must contain exactly SnapBeforeWatchTower and README.md. Found:\n' >&2
    find "$DIST_DIR" -mindepth 1 -maxdepth 1 -printf '  %f\n' >&2
    exit 1
fi

for entry in "${DIST_ENTRIES[@]}"; do
    case "$entry" in
        "$EXECUTABLE"|"$DIST_README") ;;
        *)
            printf 'Error: unexpected dist entry: %s\n' "$entry" >&2
            exit 1
            ;;
    esac
done

printf '\nBuild complete.\n'
printf 'dist contains exactly these two files:\n'
printf '  %s\n' "$EXECUTABLE" "$DIST_README"
printf '\nBasic checks:\n'
"$EXECUTABLE" --version
"$EXECUTABLE" --help >/dev/null
printf 'PyInstaller executable --help check: OK\n'
