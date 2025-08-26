Cant Save Princess — Working Plan
=================================

using bow when no targets in range consumed an arrow...


Tile Graphics Enhancement
- Add lots more types of tiles and replace the walls with them.
- Next assets to generate/place:
  - Alternate walls: `pine_wall` (taller conifers), `mossy_stone_wall` (aged interior/exterior).
  - Props: `crate`, `barrel`, `lantern` (non-collidable light source), `signpost`.
  - Interior decor: `rug`, `bench`, `bookshelf`, `counter`.
  - Ground details: `mushroom_tuft`, `flower_patch`, `fallen_log`.
  - Fences/bridges: `wooden_fence`, `short_bridge` for water crossings.
- Placement plan:
  - Forest maps: mix `pine_wall` with `tree_wall`, scatter `mushroom_tuft`, `fallen_log`.
  - Town/shop interiors: use `mossy_stone_wall`, add `rug`, `bench`, `bookshelf`, `counter`.
  - Pathing: consider a light/dark dirt `path_tile` set to guide routes.
- Notes:
  - Keep props collidability sensible (furniture collidable; decor non-collidable).
  - Prefer small, readable silhouettes at 16px; keep palette cc-29.


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

Items: Stackable + Consumables
- Add item metadata: `stackable: bool`, `consumable: bool` (and optional `max_stack`).
- On granting items:
  - If `stackable` is false, cap quantity at 1 regardless of further grants.
  - If `stackable` is true, increment count up to `max_stack` (if provided).
- On using items generically:
  - If `consumable` is true, decrement quantity by 1 on successful use.
  - After decrement, if quantity is 0, remove the item and unbind any hotkeys pointing to it.
- UI display rules:
  - For non‑stackable items, do not show a quantity suffix.
  - For stackable items, show `({qty})` only when qty > 1.
  - For items with extra state (e.g., Torch `lit/remaining`), append status before qty.

Sprites
- Regenerate `green_hero` and `sword` sprites with transparent backgrounds.
  - Use: `uv run asset generate "green_hero" "green hero" "pixel, cute" --out-size 16 --palette cc-29`
  - Use: `uv run asset generate "sword" "sword" "pixel, topdown" --out-size 16 --palette cc-29`
  - Do NOT pass `--enable-fallback`; prefer Imagen‑1 transparent output.
- Reprocess all: `uv run asset reprocess-all --out-size 16 --palette cc-29`.

Shops
- Make Town Shop use curated `sprites/shop.png` (set `sprite_name = "shop"`). [done]
