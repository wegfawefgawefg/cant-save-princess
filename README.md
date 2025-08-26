# CantSavePrincess
A small roguelike experiment, refactored to a de-OOPed architecture.

## Setup

This project uses uv to manage the environment and scripts.

1) Install uv (see uv docs)
2) Sync the environment:

```
uv sync
```

## Run

Run the game via the project console script:

```
uv run game
```

Headless (no window):

```
SDL_VIDEODRIVER=dummy uv run game
```

## Dev

- Type check:

```
uv run mypy .
```

- Lint/format with Ruff:

```
uv run ruff check .
uv run ruff format .
```

## Packaging

- Requirements: Python 3.11+, `uv`, `pygame`. Assets live in `sounds/` at repo root.
- Install build tool: `uv add --dev pyinstaller`

### Fast path (Linux)

- Onefile binary:

```
make build-linux
./dist/CantSavePrincess
```

- Onedir (easier to debug; assets visible on disk):

```
make build-linux-dir
./dist/CantSavePrincess/CantSavePrincess
```

### PyInstaller (direct commands)

- Linux/macOS:

```
uv run pyinstaller --name CantSavePrincess \
  --onefile --noconsole \
  --add-data "sounds:sounds" \
  --add-data "sprites:sprites" \
  pyi_entry.py
```

- Windows (run on Windows):

```
uv run pyinstaller --name CantSavePrincess \
  --onefile --windowed \
  --add-data "sounds;sounds" \
  --add-data "sprites;sprites" \
  pyi_entry.py
```

Notes:
- Asset loading uses `csp.assets.asset_path`, which works in dev and frozen bundles.
- For macOS Gatekeeper, you may need to notarize or use `xattr -dr com.apple.quarantine ./CantSavePrincess` for local testing.
- To reduce size, prefer `--onefile`. For easier debugging, omit `--onefile` to get an unpacked `dist/` directory.

### Troubleshooting

- No window on headless CI: use `SDL_VIDEODRIVER=dummy uv run game`.
- No audio: set `SDL_AUDIODRIVER=dummy` to skip audio, or ensure OS audio devices are available.
- Missing assets: ensure `sounds/` and `sprites/` exist relative to the binary, or that they were bundled via `--add-data`.

References:
https://inventwithpython.com/blog/2012/12/10/8-bit-nes-legend-of-zelda-map-data/
https://datacrystal.tcrf.net/wiki/The_Legend_of_Zelda/ROM_map
https://tartarus.rpgclassics.com/zelda1/1stquest/dungeonmaps.shtml
