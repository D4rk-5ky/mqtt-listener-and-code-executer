# Run directly: python -m PyInstaller --clean --noconfirm mqtt-listener.spec
# Preferred Linux wrapper: ./build-pyinstaller.sh
# Config and user-selected command scripts stay external and editable.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

project = Path(SPECPATH)
datas, binaries, hiddenimports = collect_all('paho.mqtt')
# Resolve VERSION beside the entry script in a source checkout or frozen bundle.
datas.append((str(project / 'VERSION'), '.'))
analysis = Analysis(
    [str(project / 'mqtt-listener.py')],
    pathex=[str(project)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
python_archive = PYZ(analysis.pure)
executable = EXE(
    python_archive,
    analysis.scripts,
    [('u', None, 'OPTION')],
    exclude_binaries=True,
    name='mqtt-listener',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='mqtt-listener',
)
