CantSavePrincess (csp) Migration Plan
====================================

Purpose: prepare the project for packaging and distribution while keeping uv-based dev flow.

1) Repo rename and baseline
- Rename folder to `cant-save-princess` (you are doing this).
- Keep uv workflow: `uv sync`, `uv run game`.

2) Create package `csp`
- Move code from `src/` into `src/csp/` (same module split: graphics, state, draw, movement, ai, combat, economy, commerce, items, interact, step, main).
- Update all imports to `from csp...` absolute imports.
- Update `pyproject.toml`:
  - `[project.scripts] game = "csp.main:main"` (so `uv run game` uses console entry).
  - Add package data rules if/when we embed assets.

3) Assets handling
- Keep `sounds/` at repo root for now.
- Add a frozen-safe helper `csp/assets.py` to resolve asset paths that works both in dev and frozen (PyInstaller):
  - Check `sys._MEIPASS` for frozen bundles.
  - Fallback to project-root relative `sounds/` for dev.
- Update sound loading to use this helper (no more hardcoded relative paths).

4) Packaging
- Add build script/notes for PyInstaller (fast path to binaries):
  - Dev install: `uv add --dev pyinstaller`.
  - Build (example): `uv run pyinstaller --name CantSavePrincess --onefile --noconsole --add-data "sounds:sounds" -m csp.main`.
  - Verify that the binary runs and sounds play.
- (Optional later) Evaluate Nuitka for smaller/faster binaries.

5) Tooling
- Ruff: `uv run ruff check .` then `uv run ruff format .`.
- Mypy: `uv run mypy src` (and later `uv run mypy .` after package move).
- Ensure VS Code uses `.venv/bin/python` and Ruff on save (already configured).

6) README updates
- Update run instructions remain `uv run game`.
- Add a short Packaging section with the PyInstaller command and notes about assets.

7) Sanity checks
- Run locally: `uv run game`.
- Headless quick test: `SDL_VIDEODRIVER=dummy uv run game` (no window; just to catch import errors).

8) Stretch (post-migration)
- Consider splitting entity definitions/types and adding stricter mypy rules.
- Add basic CI (ruff + mypy) if desired.

Deliverables during next session
- Perform step 2 (package move) + step 3 (asset helper) + step 5 checks + step 6 README updates.
- Optional: wire the PyInstaller script/notes (step 4).

