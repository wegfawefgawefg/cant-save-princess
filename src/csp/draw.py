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
from csp.state import State, all_entities


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
        f"Rabbit Corpses: {state.player.meat}",
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

    # Inventory under binds
    inv_y = left_y + 20 + len(binds_list) * 18 + 16
    screen.blit(font.render("Inventory:", True, COLORS["text"]), (left_x, inv_y))
    inv_y += 18
    if state.owned_items:
        for name, qty in list(state.owned_items.items())[:12]:
            line = f" {name}: {qty}"
            screen.blit(font.render(line, True, COLORS["text"]), (left_x, inv_y))
            inv_y += 16
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

    # Draw walls
    for wall in state.map_walls:
        wx, wy = wall
        # Only draw if within view bounds
        if not (cam_x <= wx < cam_x + view_w and cam_y <= wy < cam_y + view_h):
            continue
        pygame.draw.rect(
            screen,
            COLORS["wall"],
            (
                GAME_OFFSET_X + (wx - cam_x) * CELL_SIZE,
                (wy - cam_y) * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE,
            ),
        )

    # Draw entities (non-player first)
    for e in all_entities(state):
        if e is state.player:
            continue
        if not (cam_x <= e.x < cam_x + view_w and cam_y <= e.y < cam_y + view_h):
            continue
        pygame.draw.circle(
            screen,
            e.color,
            (
                GAME_OFFSET_X + (e.x - cam_x) * CELL_SIZE + CELL_SIZE // 2,
                (e.y - cam_y) * CELL_SIZE + CELL_SIZE // 2,
            ),
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
    pygame.draw.circle(
        screen,
        COLORS["player"],
        (
            GAME_OFFSET_X + (state.player.x - cam_x) * CELL_SIZE + CELL_SIZE // 2,
            (state.player.y - cam_y) * CELL_SIZE + CELL_SIZE // 2,
        ),
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
        "Enter: Buy  |  Esc: Quit (dev)",
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
    start_y = 140
    for i, (name, qty) in enumerate(items):
        selected = i == state.menu_inventory_index
        color = (255, 215, 0) if selected else COLORS["text"]
        line = f"{name} x{qty}"
        prefix = "> " if selected else "  "
        _draw_centered_text(screen, font, prefix + line, start_y + i * 28, color)
    _draw_centered_text(
        screen,
        font,
        "Press number to bind. Esc: Quit (dev)",
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
