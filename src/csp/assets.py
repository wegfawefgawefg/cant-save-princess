from __future__ import annotations

import sys
from pathlib import Path


def asset_path(relative: str) -> Path:
    """Resolve an asset path for dev and frozen builds.

    - Frozen (PyInstaller): assets are bundled under sys._MEIPASS.
    - Dev: resolve relative to the project root, where "sounds/" lives.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / relative

    # Project root: .../repo (since this file is .../repo/src/csp/assets.py)
    project_root = Path(__file__).resolve().parents[2]
    return project_root / relative
