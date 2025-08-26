from __future__ import annotations

import pygame

from csp.graphics import (
    CELL_SIZE,
    COLORS,
    COLS,
    GAME_OFFSET_X,
    LEFT_PANEL_WIDTH,
    PANEL_WIDTH,
    ROWS,
    SCREEN_SIZE,
)
from csp.state import State, all_entities, GameMode
from csp.sprites import load_sprite_for_entity, load_sprite_for_name


def draw_grid(state: State, screen: pygame.Surface, cam_x: int, cam_y: int) -> None:
    # Draw grid only over the visible portion of the current map
    view_w, view_h = COLS, ROWS
    map_w, map_h = state.map_cols, state.map_rows
    x_min_map = max(cam_x, 0)
    x_max_map = min(cam_x + view_w, map_w)
    y_min_map = max(cam_y, 0)
    y_max_map = min(cam_y + view_h, map_h)

    # Vertical lines
    for ix in range(x_min_map, x_max_map + 1):
        x = GAME_OFFSET_X + (ix - cam_x) * CELL_SIZE
        y1 = (y_min_map - cam_y) * CELL_SIZE
        y2 = (y_max_map - cam_y) * CELL_SIZE
        pygame.draw.line(screen, COLORS["grid"], (x, y1), (x, y2))
    # Horizontal lines
    for iy in range(y_min_map, y_max_map + 1):
        y = (iy - cam_y) * CELL_SIZE
        x1 = GAME_OFFSET_X + (x_min_map - cam_x) * CELL_SIZE
        x2 = GAME_OFFSET_X + (x_max_map - cam_x) * CELL_SIZE
        pygame.draw.line(screen, COLORS["grid"], (x1, y), (x2, y))


def draw_ui(state: State, screen: pygame.Surface, font: pygame.font.Font) -> None:
    panel_x = LEFT_PANEL_WIDTH + COLS * CELL_SIZE + 10
    stats = [
        f"Gold: {state.player.gold}",
        f"Rabbit Meat: {int(state.owned_items.get('Rabbit Meat', 0))}",
        f"Pig Meat: {int(state.owned_items.get('Pig Meat', 0))}",
        f"Bear Meat: {int(state.owned_items.get('Bear Meat', 0))}",
        f"Health: {state.player.health}",
        f"Turn: {state.turn_count}",
        "-------",
        "[H] Help",
        "[P] Punch",
        "[S] Shop/Talk",
        "[L] Labels",
        "[I] Inventory",
        "[Space] Interact",
    ]
    # Draw stats
    for i, text in enumerate(stats):
        screen.blit(font.render(text, True, COLORS["text"]), (panel_x, 10 + i * 20))

    # Draw binds on left panel
    left_x = 10
    left_y = 10
    screen.blit(font.render("Binds:", True, COLORS["text"]), (left_x, left_y))
    binds_list = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
    for i, k in enumerate(binds_list):
        label = state.binds.get(k, "-")
        txt = f" {k}: {label}"
        screen.blit(font.render(txt, True, COLORS["text"]), (left_x, left_y + 20 + i * 18))

    # Inventory under binds (show icons and bound slot numbers)
    inv_y = left_y + 20 + len(binds_list) * 18 + 16
    screen.blit(font.render("Inventory:", True, COLORS["text"]), (left_x, inv_y))
    inv_y += 18
    # Inventory entries: owned items; annotate Torch with lit/remaining from item state
    entries: list[tuple[str, int]] = [(k, int(v)) for k, v in state.owned_items.items() if int(v) > 0]
    if entries:
        # Reverse map: item name -> bound slot key (e.g., '1')
        bound_slot: dict[str, str] = {}
        for slot, iname in state.binds.items():
            if iname:
                bound_slot[iname] = slot
        # Draw up to 12 entries
        for name, qty in entries[:12]:
            slot_txt = bound_slot.get(name)
            # Annotate Torch with lit/remaining if present
            if name == "Torch":
                tdata = state.player.inventory.get("Torch")
                if isinstance(tdata, dict):
                    try:
                        rem = int(tdata.get("remaining", 0))
                    except Exception:
                        rem = 0
                    lit = bool(tdata.get("lit", False))
                    status = "lit" if lit else "unlit"
                    label = f" Torch ({status}) [{rem}] ({qty})"
                else:
                    label = f" {name} ({qty})"
            else:
                label = f" {name} ({qty})"
            if slot_txt:
                label = f" [{slot_txt}]" + label
            # Try icon
            try:
                from csp.sprites import load_sprite_for_name

                icon = load_sprite_for_name(name)
            except Exception:
                icon = None
            if icon is not None:
                screen.blit(icon, (left_x, inv_y - 1))
                text_x = left_x + icon.get_width() + 6
            else:
                text_x = left_x
            screen.blit(font.render(label, True, COLORS["text"]), (text_x, inv_y))
            inv_y += max(16, (icon.get_height() if icon is not None else 0)) or 16
    else:
        screen.blit(font.render(" (empty)", True, COLORS["text"]), (left_x, inv_y))

    # Draw message log below stats on the right, with simple wrapping
    offset = 300
    max_w = PANEL_WIDTH - 20
    y = offset
    max_y = ROWS * CELL_SIZE - 10
    # Flatten wrapped lines and show the most recent lines at the bottom
    all_lines: list[tuple[str, int]] = []
    for msg, when in state.message_log:
        wrapped = _wrap_text(font, msg, max_w)
        for w in wrapped:
            all_lines.append((w, when))
    line_h = 20
    max_lines = (max_y - offset) // line_h
    recent = all_lines[-max_lines:]
    start_y = max(offset, max_y - len(recent) * line_h)
    y = start_y
    for text, when in recent:
        # Bright for current-turn messages, dim for older
        if when == state.turn_count:
            color = (255, 255, 255)
        else:
            color = (200, 200, 200)
        screen.blit(font.render(text, True, color), (panel_x, y))
        y += line_h


def draw_help(screen: pygame.Surface, font: pygame.font.Font) -> None:
    help_text = [
        "Controls:",
        "Arrow Keys: Move",
        "H: Toggle Help",
        "P: Punch (adjacent)",
        "S: Shop/Talk (trapper or item shop)",
        "Space: Interact (chest, lever, etc.)",
        "1: Use Sword (if owned)",
        "2: Use Bow (if owned)",
        "L: Toggle on-screen labels",
    ]
    overlay = pygame.Surface((SCREEN_SIZE[0], SCREEN_SIZE[1]))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    for i, line in enumerate(help_text):
        screen.blit(font.render(line, True, COLORS["text"]), (50, 50 + i * 20))


def draw_frame(state: State, screen: pygame.Surface, font: pygame.font.Font) -> None:
    """Draws the gameplay scene (when in PLAYING mode)."""
    screen.fill(COLORS["background"])

    # Camera in tile coords. Center on player, clamp to map; center small maps.
    view_w, view_h = COLS, ROWS
    map_w, map_h = state.map_cols, state.map_rows
    # Default center camera on player
    cam_x = state.player.x - view_w // 2
    cam_y = state.player.y - view_h // 2
    # Clamp to map bounds
    cam_x = max(0, min(cam_x, max(0, map_w - view_w)))
    cam_y = max(0, min(cam_y, max(0, map_h - view_h)))
    # If map smaller than view, center it by allowing negative cam offsets
    if map_w < view_w:
        cam_x = -(view_w - map_w) // 2
    if map_h < view_h:
        cam_y = -(view_h - map_h) // 2

    # Draw plain collidable tiles (no sprite) as wall rects
    for (tx, ty), tile in state.map_tiles.items():
        if not tile.collidable or tile.sprite is not None:
            continue
        if not (cam_x <= tx < cam_x + view_w and cam_y <= ty < cam_y + view_h):
            continue
        pygame.draw.rect(
            screen,
            COLORS["wall"],
            (
                GAME_OFFSET_X + (tx - cam_x) * CELL_SIZE,
                (ty - cam_y) * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE,
            ),
        )

    # Draw tile images (non-grid visuals like torches/leaves)
    for (tx, ty), tile in list(state.map_tiles.items()):
        if tile.sprite is None:
            continue
        if not (cam_x <= tx < cam_x + view_w and cam_y <= ty < cam_y + view_h):
            continue
        spr = load_sprite_for_name(tile.sprite)
        if spr is not None:
            sx = GAME_OFFSET_X + (tx - cam_x) * CELL_SIZE
            sy = (ty - cam_y) * CELL_SIZE
            screen.blit(spr, (sx, sy))

    # Draw entities (non-player first)
    for e in all_entities(state):
        if e is state.player:
            continue
        if not (cam_x <= e.x < cam_x + view_w and cam_y <= e.y < cam_y + view_h):
            continue
        sx = GAME_OFFSET_X + (e.x - cam_x) * CELL_SIZE
        sy = (e.y - cam_y) * CELL_SIZE
        spr = load_sprite_for_entity(e)
        if spr is not None:
            screen.blit(spr, (sx, sy))
        else:
            pygame.draw.circle(
                screen,
                e.color,
                (sx + CELL_SIZE // 2, sy + CELL_SIZE // 2),
                CELL_SIZE // 2,
            )
        if state.show_labels:
            label = f"{e.name}"
            lbl_surf = font.render(label, True, (255, 255, 255))
            screen.blit(
                lbl_surf,
                (GAME_OFFSET_X + (e.x - cam_x) * CELL_SIZE, (e.y - cam_y) * CELL_SIZE - 10),
            )

    # Draw player last
    psx = GAME_OFFSET_X + (state.player.x - cam_x) * CELL_SIZE
    psy = (state.player.y - cam_y) * CELL_SIZE
    pspr = load_sprite_for_entity(state.player)
    if pspr is not None:
        screen.blit(pspr, (psx, psy))
    else:
        pygame.draw.circle(
            screen,
            COLORS["player"],
            (psx + CELL_SIZE // 2, psy + CELL_SIZE // 2),
            CELL_SIZE // 2,
        )
    if state.show_labels:
        label = f"{state.player.name}"
        lbl_surf = font.render(label, True, (255, 255, 255))
        screen.blit(
            lbl_surf,
            (
                GAME_OFFSET_X + (state.player.x - cam_x) * CELL_SIZE,
                (state.player.y - cam_y) * CELL_SIZE - 10,
            ),
        )

    # Grid only over the visible map area
    draw_grid(state, screen, cam_x, cam_y)
    draw_ui(state, screen, font)
    if state.show_help:
        draw_help(screen, font)

    # Map name label at bottom of play area
    if state.current_map_id and state.current_map_id in state.maps:
        name = state.maps[state.current_map_id].name
        label_surf = font.render(name, True, COLORS["text"])
        lx = GAME_OFFSET_X + (COLS * CELL_SIZE - label_surf.get_width()) // 2
        ly = ROWS * CELL_SIZE - label_surf.get_height() - 4
        screen.blit(label_surf, (lx, ly))

    # Death overlay
    if state.mode == GameMode.DEAD:
        overlay = pygame.Surface((COLS * CELL_SIZE, ROWS * CELL_SIZE), pygame.SRCALPHA)
        overlay.fill((80, 0, 0, 160))
        screen.blit(overlay, (GAME_OFFSET_X, 0))
        _draw_centered_text(screen, font, "You Died", 120, (255, 80, 80))
        _draw_centered_text(screen, font, "Press I for Inventory", 160, COLORS["text"])


def _draw_centered_text(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    y: int,
    color: tuple[int, int, int] = (220, 220, 220),
) -> None:
    surf = font.render(text, True, color)
    x = (SCREEN_SIZE[0] - surf.get_width()) // 2
    screen.blit(surf, (x, y))


def _wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        test = cur + " " + w
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def draw_main_menu(state: State, screen: pygame.Surface, font: pygame.font.Font) -> None:
    screen.fill(COLORS["background"])
    title_font = font
    _draw_centered_text(screen, title_font, "Cant Save Princess", 120, COLORS["text"])

    options = ("Play", "Settings", "Quit")
    start_y = 200
    for i, label in enumerate(options):
        selected = i == state.menu_main_index
        color = (255, 215, 0) if selected else COLORS["text"]
        prefix = "> " if selected else "  "
        _draw_centered_text(screen, font, prefix + label, start_y + i * 30, color)


def draw_settings_menu(state: State, screen: pygame.Surface, font: pygame.font.Font) -> None:
    screen.fill(COLORS["background"])
    _draw_centered_text(screen, font, "Settings", 120, COLORS["text"])
    options = ("Back",)
    start_y = 200
    for i, label in enumerate(options):
        selected = i == state.menu_settings_index
        color = (255, 215, 0) if selected else COLORS["text"]
        prefix = "> " if selected else "  "
        _draw_centered_text(screen, font, prefix + label, start_y + i * 30, color)


def draw_shop_menu(state: State, screen: pygame.Surface, font: pygame.font.Font) -> None:
    screen.fill(COLORS["background"])
    _draw_centered_text(screen, font, "Shop", 80, COLORS["text"])
    items = state.shop_inventories.get(state.active_shop_id or "", [])
    if not items:
        _draw_centered_text(screen, font, "No items", 130, COLORS["text"])
        return
    start_y = 140
    for i, it in enumerate(items):
        selected = i == state.menu_shop_index
        color = (255, 215, 0) if selected else COLORS["text"]
        name = it["name"]
        cost = it["cost"]
        max_qty = it["max_qty"]
        purchased = it.get("purchased", 0)
        stock_txt = "∞" if max_qty is None else f"{purchased}/{max_qty}"
        owned = state.owned_items.get(name, 0)
        line = f"{name} - {cost}g  [{stock_txt}]  (own: {owned})"
        prefix = "> " if selected else "  "
        _draw_centered_text(screen, font, prefix + line, start_y + i * 28, color)
    _draw_centered_text(
        screen,
        font,
        "Enter: Buy  |  Esc: Quit",
        start_y + len(items) * 28 + 20,
        COLORS["text"],
    )


def draw_inventory_menu(state: State, screen: pygame.Surface, font: pygame.font.Font) -> None:
    screen.fill(COLORS["background"])
    _draw_centered_text(screen, font, "Inventory (press 1..0 to bind)", 80, COLORS["text"])
    items = sorted(state.owned_items.items())
    if not items:
        _draw_centered_text(screen, font, "No items owned.", 130, COLORS["text"])
        return
    # Reverse map for bound slot display
    rev_bind: dict[str, str] = {v: k for k, v in state.binds.items() if v}
    start_y = 140
    for i, (name, qty) in enumerate(items):
        selected = i == state.menu_inventory_index
        color = (255, 215, 0) if selected else COLORS["text"]
        slot = rev_bind.get(name)
        slot_txt = f" [{slot}]" if slot else ""
        line = f"{name}{slot_txt} x{qty}"
        prefix = "> " if selected else "  "
        _draw_centered_text(screen, font, prefix + line, start_y + i * 28, color)
    _draw_centered_text(
        screen,
        font,
        "Press number to bind. Esc: Quit",
        start_y + len(items) * 28 + 20,
        COLORS["text"],
    )


def draw_dialogue(state: State, screen: pygame.Surface, font: pygame.font.Font) -> None:
    # Simple overlay with text and options
    overlay = pygame.Surface((COLS * CELL_SIZE, ROWS * CELL_SIZE), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (GAME_OFFSET_X, 0))

    if not state.dialogue_id or not state.dialogue_node:
        return
    tree = state.dialogues.get(state.dialogue_id, {})
    nodes = tree.get("nodes", {})
    node = nodes.get(state.dialogue_node, {})
    text = str(node.get("text", ""))
    options = node.get("options", [])

    # Wrap not implemented; render lines stacked
    lines = [text]
    for i, opt in enumerate(options):
        prefix = "> " if i == state.menu_dialogue_index else "  "
        lines.append(prefix + str(opt.get("label", "")))

    start_y = 120
    for i, line in enumerate(lines):
        _draw_centered_text(screen, font, line, start_y + i * 22, COLORS["text"])
