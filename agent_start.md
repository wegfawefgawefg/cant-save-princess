Agent Start Guide
=================

Project: CantSavePrincess

What this project is
- A small top‑down roguelike‑ish prototype in Python using pygame.
- Rendering currently supports tile grid, simple shapes, and now sprites.
- Assets live at repo root under: `sprites/`, `unshrunk_sprites/`, `sounds/`, `palettes/`.

check the docs and game_design folders for more info about areas and design. 

**Development Philosophy**
- **Data first:** Tiles and entities are plain data records. No inheritance hierarchies or object graphs beyond simple containers like `Tile`, `Entity`, and `State`.
- **No registries/callbacks:** We do not register per‑tile handlers or maintain special lists (e.g., traps, interactables). All tiles live in `state.map_tiles` and are inspected by logic functions.
- **Central responders:** Game behavior lives in a few clear functions:
  - Movement/step triggers: `map_runtime.process_triggers_after_move`
  - Interaction: `interact.handle_interact`
  - Combat: `combat.handle_combat`/`perform_attack`
  - Items: `items.use_item`
- **Branch where needed:** If a specific tile in a specific map needs custom behavior, branch in the responder using `state.current_map_id`, position, or `Tile.tag`. Simplicity > abstraction.
- **Flags for persistence:** Use `flags.set_flag` and `has_flag` to persist outcomes (doors opened, enemies dead) across loads.
- **Scoped flags:** Prefer `scope='map'` for flags that only apply to the current map instance; use `scope='global'` for world state that must persist across maps and sessions. Map‑scoped flags are cleared on load.
- **Pure-ish functions:** Prefer functions that take `state` and mutate it directly. Avoid hidden side‑effects, global singletons, or implicit callbacks.

Main entry
- Run game: `uv run game` (pyproject `project.scripts` → `csp.main:main`).
- Window: 960×540 play area plus side panels, default 60 FPS.

Sprite generation tooling
- Tool: `tools/gen_asset_image.py` (wrapper exists at root `gen_asset_image.py`).
- uv shortcuts (pyproject `[tool.uv.scripts]`):
  - `uv run asset generate <name> <thing> [description] [--out-size 16] [--palette cc-29] [--enable-fallback]`
  - `uv run asset reprocess-all [--out-size 16] [--palette cc-29]` (wipes `sprites/` first)

Conventions
- Originals are saved to `unshrunk_sprites/<name>.png` (square 1024×1024).
- Sprites are written to `sprites/<name>.png` at the requested size (default 32; we typically use 16).
- Palette files: `palettes/<name>.hex` (RRGGBB or RRGGBBAA per line). `cc-29.hex` exists.
- The tool requests transparent PNGs when using `gpt-image-1`. If permissions block that model, use `--enable-fallback` to permit fallback (may be opaque).

How the game finds sprites
- For each entity, we try `sprites/<slug(name)>.png` where slug is lowercase with non‑alphanumerics → `_`.
- Entities may set `sprite_name` to override (e.g., `Player.sprite_name = "green_hero"`, `Item Shop.sprite_name = "shop"`).
- If a sprite is missing, rendering falls back to the previous circle marker.

Rendering system
- Added `csp.sprites` for loading and scaling sprites to tile size (`CELL_SIZE`).
- `csp.draw.draw_frame` now attempts to blit sprite surfaces for entities and the player.
- Labels are enabled by default (can toggle in game with `L`).

Map conditionals and flags
- Use `csp.flags.set_flag(state, name, scope='global', duration_steps=None)` for unexpiring flags.
- Maps can define `on_load(state)` in `MapDef` which runs once after a map is loaded into runtime.
- Helpers in `csp.map_helpers`:
  - `hide_by_behavior_if_flag(state, behavior, flag)` — remove entities with a behavior when a flag is set.
  - `hide_by_name_if_flag(state, names, flag)` — remove entities by name when a flag is set.
- Example: a gold pickup sets `gold_taken` globally on interact; riddle room `on_load` hides `behavior='gold'` when that flag exists.
 - Scoping notes: map-scoped flags are cleared on map unload. For global flags that conceptually belong to a specific map, namespace them (e.g., `forest_a.bear_dead`) to keep the global namespace tidy.

Gameplay helpers
- `csp.gameplay.grant_gold(state, amount, source=None)` — add gold and log.
- `csp.gameplay.damage_player(state, amount, source=None)` — damage and log; sets DEAD mode when health <= 0.
- `csp.gameplay.hit_sfx(state, key)` — play a sound if present.

Handy generation examples
- `uv run asset generate "hero" "little green hero" "cute + bouncy" --out-size 16 --palette cc-29 --enable-fallback`
- `uv run asset generate "bunny" "white rabbit" "cute, bouncy" --out-size 16 --palette cc-29 --enable-fallback`
- `uv run asset reprocess-all --out-size 16 --palette cc-29`

Notes for agents
- Prefer generating assets with the tool over drawing placeholders.
- Keep filenames simple (slug name). Avoid size/palette suffixes.
- When adding new entities, either name them to match a sprite filename or set `entity.sprite_name`.
- If `gpt-image-1` remains blocked, you may use `--enable-fallback`, but for curated sprites (e.g., hero, sword) prefer strict generation without fallback to avoid opaque backgrounds.
- Editor tooling: Use Pylance in VS Code (driven by `pyrightconfig.json`) for fast type hints and diagnostics.

**Tiles & Interactions**
- **Storage:** All tiles are stored in `state.map_tiles: dict[(x, y) -> Tile]`. No separate trap/interactable collections.
- **Creation:** `map_runtime.load_map` populates walls/solids as collidable `Tile`s. A map's optional `on_load(state)` may add or modify tiles for that map instance.
- **Movement triggers:** `map_runtime.process_triggers_after_move(state)` inspects the player’s current tile (e.g., `tag == 'leaves'`) and applies effects. Remove/replace tiles by editing `state.map_tiles` directly.
- **Interactions:** `interact.handle_interact(state, preferred_dir)` inspects adjacent tiles/entities and runs logic. Add small, explicit branches for special cases (e.g., a torch tile in `riddle_room`).
- **Semantics:** Use lightweight fields like `Tile.tag` and `Entity.behavior` to signal intent; avoid per‑type classes or event buses.

**Items & Per‑Item State**
- Keep items as plain data and store item‑specific state with the item (or in an `inventory_state` dict keyed by item id/name).
- Torch example: Instead of a global `player.torch_lit` flag, represent torches like `{ name: 'Torch', lit: true, remaining: 1000 }` and decrement `remaining` each turn. Rendering/vision logic should consult lit torches from inventory.
- Use flags for world changes (e.g., “bear dead”, “door open”), and item state for player equipment and timers.


Maps & Areas Spec
==================

Map Model
- Map: `id`, `name`, `size (w,h)`, `tiles`, `entities`, `step(map_state, state)` hook.
- Registry: `state.maps[map_id]` with definitions, and `state.current_map_id`.
- Load flow: `load_map(map_id, spawn_pos?)` sets `state.current_map_id`, loads tiles into `state.tiles`, spawns map entities, positions player (only persistent entity), clears per-map flags and debug shapes.
- Global step runs every tick; calls current map’s `step` hook.

Tiles
- Tile types include floor, wall, warp, interactables, etc.
- Warp tile fields: `target_map_id`, `target_pos (x,y)`, optional `sideexit_dir`.
- Side exit: if player stands on tile and presses matching direction, warp triggers (uses `sideexit_dir`). If not set, warp always triggers on enter (or via interact, tbd).

Entities
- Each map lists entities to instantiate on load (NPCs, spawners, props).
- Player persists across maps; all other entities belong to the current map.
