from __future__ import annotations

import sys
from pathlib import Path


# Ensure the src/ directory is on sys.path for module discovery during PyInstaller analysis.
SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from csp.main import main


if __name__ == "__main__":
    main()

