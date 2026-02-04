# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['texas_holdem\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['texas_holdem.core.card', 'texas_holdem.core.deck', 'texas_holdem.core.hand', 'texas_holdem.core.player', 'texas_holdem.core.table', 'texas_holdem.core.evaluator', 'texas_holdem.game.game_state', 'texas_holdem.game.betting', 'texas_holdem.game.game_engine', 'texas_holdem.ui.cli', 'texas_holdem.utils.constants'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='德州扑克',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
