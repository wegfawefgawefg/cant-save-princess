Cant Save Princess — Working Plan
=================================

put that we can use pylance/ruff, etc in the agent_start.md

Debug Shapes
- Toggle: `state.debug_shapes_on`.
- Per frame list: `state.debug_shapes` (cleared each frame).
- Shape: `{type: 'rect'|'circle'|'text', aabb/pos, color, label}`.
- Map step can push shapes to visualize conditions (e.g., region AABBs, state of checks in red/green).

for example a map step could put a yellow transparent rect in its warp tiles. or on hidden areas we want to mark or something.

Tile Graphics Enhancement
- add lots more types of tiles and replace the walls with them. 


Forest Enhancement
- add more diverse flora and fauna.
- enhance ground textures and add undergrowth details.
- wals should be tree tiles of various types

Combat enhancement:
make the bear and pig not take damage from punching at all.
make the player need a weapon that has damage 2 or higher
bow should do 2 if shoot regular arrow. 
sword can do 3. 
make the bear tanky. the bear should be tough to kill. likely to kill you. 

Sounds enhancement:
tool to make sounds
lots more sounds. music for some maps. 
if map has a music thats different than one curerntly playing
fade out current music, fade in maps music. 

visual enhancement:
lighting system where thers light values, and some tiles emit light. maps can have a base light level. 
so some areas are just day time, and some are dark. 
forest should be a little dark but not that dark. 

some moving light lines running from the top of the map to random posiiton that paints higher light values each frame would be cool. would be like light coming in through the trees

enhance the way death works if not already like this
add an on death function. which anything can happen inside.
and in there we can check like what the current map is from state or if the dead thing was a bear



Docs & Philosophy
- Document data‑first design (no per‑tile registries; central responders). [agent_start.md]
- Add scoped flags guidance (prefer `scope='map'` when appropriate) and Pylance note.

Items & Torch State
- Design per‑item state in inventory (e.g., Torch: `lit`, `remaining`).
- Replace global `player.torch_lit` flag with item‑state driven lighting and per‑turn decrement.
- Ensure draw/vision consults lit torches from inventory state.

Sprites
- Regenerate `green_hero` and `sword` sprites with transparent backgrounds.
  - Use: `uv run asset generate "green_hero" "green hero" "pixel, cute" --out-size 16 --palette cc-29`
  - Use: `uv run asset generate "sword" "sword" "pixel, topdown" --out-size 16 --palette cc-29`
  - Do NOT pass `--enable-fallback`; prefer Imagen‑1 transparent output.
- Reprocess all: `uv run asset reprocess-all --out-size 16 --palette cc-29`.

Shops
- Make Town Shop use curated `sprites/shop.png` (set `sprite_name = "shop"`). [done]
