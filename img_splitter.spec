# PyInstaller build definition for the graphical application.
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_dir = Path(SPECPATH)
datas = [
    (
        str(project_dir / "src" / "img_splitter" / "gui" / "theme"),
        "img_splitter/gui/theme",
    ),
    (
        str(project_dir / "src" / "img_splitter" / "gui" / "translations"),
        "img_splitter/gui/translations",
    ),
]

# scipy, numpy and scikit-learn are covered by PyInstaller's hooks. collect_all
# makes the build resilient to optional runtime modules used by these packages.
datas += collect_all("scipy")[0]
datas += collect_all("sklearn")[0]
binaries = collect_all("scipy")[1] + collect_all("sklearn")[1]
hiddenimports = collect_all("scipy")[2] + collect_all("sklearn")[2]


a = Analysis(
    [str(project_dir / "launcher.py")],
    pathex=[str(project_dir / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="img-splitter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
