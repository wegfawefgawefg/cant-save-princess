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

- Dev install: `uv add --dev pyinstaller`
- Build with Makefile (Linux):

```
make build-linux
./dist/CantSavePrincess
```

- Direct PyInstaller command (Linux/macOS):

```
uv run pyinstaller --name CantSavePrincess \
  --onefile --noconsole \
  --add-data "sounds:sounds" \
  pyi_entry.py
```

The game loads assets via `csp.assets.asset_path`, which supports both dev and frozen runs.

- Windows build (run on Windows):

```
uv run pyinstaller --name CantSavePrincess \
  --onefile --windowed \
  --add-data "sounds;sounds" \
  pyi_entry.py
```

References:
https://inventwithpython.com/blog/2012/12/10/8-bit-nes-legend-of-zelda-map-data/
https://datacrystal.tcrf.net/wiki/The_Legend_of_Zelda/ROM_map
https://tartarus.rpgclassics.com/zelda1/1stquest/dungeonmaps.shtml
