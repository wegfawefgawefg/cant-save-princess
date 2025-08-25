Cant Save Princess — Working Plan
=================================

Completed
- Modes and routing: MAIN_MENU, SETTINGS, PLAYING, SHOP, INVENTORY.
- Menu UX: Arrow-only navigation; bow.mp3 on move (KEYDOWN); punch.mp3 on confirm.
- Dev QoL: Ctrl+Q super quit; Esc works as Back in sub-views.
- Shop system: Registry-based (`state.shop_inventories[shop_id]`), `do_shop(id)` to open, `register_shop(id, items)` to seed.
- Item shop: Seeded Sword (1x), Bow (1x), Arrows (cheap, unlimited); Bow consumes Arrows.
- Inventory & binds: Inventory screen, bind with 1..0, binds shown on left panel.
- HUD/layout: Left panel for binds; right panel for stats/actions; messages moved below to avoid overlap.

Needs Validation / Polishing
- Message log layout: confirm desired max lines, truncation vs wrap, and spacing so it never collides with other panels.
- Multi-vendor examples: register and wire additional shops in-world as needed.

Next Up
1) Square playfield and finalize panel dimensions.
2) Icons: map items → icon assets; render in HUD/Inventory/Shop. Dev-only generator tool later (not a game feature).
3) Trapper view: design together first (what actions/trades/limits), then implement (could reuse shop registry or a custom trade UI).
4) Optional UX: explicit “Back” row in SHOP/INVENTORY (Enter to leave) alongside Esc.
5) Expand Settings content or hide until used.
6) Implement Maps/Warps/Flags/Debug/Dialogue per spec below.
7) Add Death/Game Over flow (overlay + return to menu).

Sound Mapping (reference)
- Move (menus/shop/inventory): bow.mp3
- Purchase success: punch.mp3
- Purchase fail / insufficient: grunt.mp3

Notes
- Registry approach avoids passing items at open-time; use `register_shop(...)` once and `do_shop(id)` to open.
- Trapper view remains pending design; capture details here before coding.

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

Steps
- Global step: handles timers, economy, AI, input routing.
- Map step: per-map logic (spawns, scripted events, area checks using flags and debug shapes).

Flags System
- Class: `Flag(name: str, scope: ('global'|'map'), timer: int|None)`.
- Helpers:
  - `set_flag(name, scope='map', timer=None)` (optionally for a specific map).
  - `unset_flag(name)`.
  - `has_flag(name)` checks appropriate scope (global or current map).
- Timers decrement in global step; when reaching 0, flag unsets.
- Map-scoped flags auto-unset on map switch; global flags persist.

Debug Shapes
- Toggle: `state.debug_shapes_on`.
- Per frame list: `state.debug_shapes` (cleared each frame).
- Shape: `{type: 'rect'|'circle'|'text', aabb/pos, color, label}`.
- Map step can push shapes to visualize conditions (e.g., region AABBs, state of checks in red/green).

Dialogue Trees
- Mode: `DIALOGUE` with its own input/render.
- Registry: `state.dialogues[tree_id]`.
- Node: `{id, text, options: [{label, next_id|action, requires?, sets?}], backoutable?: bool}`.
- Navigation: arrows to move, Enter/Space select (punch.mp3), bow.mp3 on move, Esc backs out if allowed.
- Actions: call functions (e.g., open shop, trade meat) or set flags.

Initial Areas
- Start Area: small zone with a sign; interacting shows a sign view: “North: Town, East: Woods, South: Sea”. East leads to Woods Entrance.
- Woods Entrance: contains Lazy Trapper NPC; if no meat → remark; else opens a choice menu (Yes give meat / No) leading to actions (trade meat → gold via action). To the right: trees, then bunny spawn zone with several bunny holes.
- Test Zone (to the left): playground for experimental features, debug shapes, etc.
- Future: Town (north), Beach/Sea (south) later.

Transitions
- Use warp tiles with optional `sideexit_dir` for directional exits.
- Borders can be solid walls; place explicit warp tiles for transitions.

Open Question: Edge Warps vs Transition Tiles
- Option A (recommended): Solid borders + explicit transition tiles (clear UX, avoids accidental border crossings, easier to theme visuals).
- Option B: Edge warp tiles (saves tiles, but can look/feel abrupt and cause accidental transitions).
- We plan A unless we choose otherwise during layout polish.

Death / Game Over
=================

Goal
- When player dies, they become uncontrollable; a big red “YOU DIED” overlay appears.
- After 2 seconds, prompt shows “Press Enter/Space to continue”. Confirm returns to Main Menu.

Spec
- Add mode: `GAME_OVER`.
- On death trigger (player.health <= 0):
  - Record timestamp/frame: `death_time`.
  - Switch to `GAME_OVER` mode; freeze gameplay input/AI.
- Rendering:
  - Dim screen overlay.
  - Centered large red text: “YOU DIED”.
  - After 2s: show smaller prompt: “Press Enter/Space to continue”.
- Input:
  - Before 2s: ignore Enter/Space.
  - After 2s: Enter/Space transitions to `MAIN_MENU`.
- State reset: decide whether to reset the world/player on return to Main Menu (recommended: full fresh `State()` on starting Play again).
- Sounds: optional death sting (tbd).
