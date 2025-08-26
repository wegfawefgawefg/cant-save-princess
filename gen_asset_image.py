#!/usr/bin/env python3
"""
Compatibility wrapper for tools/gen_asset_image.py

Usage remains the same, but canonical code lives in tools/.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "tools" / "gen_asset_image.py"
if not SCRIPT.exists():
    print(f"Error: missing script at {SCRIPT}", file=sys.stderr)
    sys.exit(1)

runpy.run_path(str(SCRIPT), run_name="__main__")

