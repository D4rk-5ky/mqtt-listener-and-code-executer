# Run: python -m PyInstaller --clean --noconfirm mqtt-listener.spec
# Config and user-selected command scripts stay external and editable.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

project = Path(SPECPATH)
datas, binaries, hiddenimports = collect_all('paho.mqtt')
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
    analysis.binaries,
    analysis.datas,
    [('u', None, 'OPTION')],
    name='mqtt-listener',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
