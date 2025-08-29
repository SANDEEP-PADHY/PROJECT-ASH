# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\zenon\\Downloads\\PROJECT-ASH'],
    binaries=[],
    datas=[
        ('CODE MONK LOGO.png', '.'),
        ('app.ico', '.'),
    ],
    hiddenimports=[
        'gui',
        'secure_wipe',
        'certificate',
        'drive_utils',
        'utils',
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'reportlab.pdfgen.canvas',
        'reportlab.lib.pagesizes',
        'PIL.Image',
        'wmi',
        'psutil',
        'win32api',
        'win32gui',
        'win32con'
    ],
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
    name='CodeMonk_SecureFormatter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',
    uac_admin=True,  # Request administrator privileges
    uac_uiaccess=False,
)
