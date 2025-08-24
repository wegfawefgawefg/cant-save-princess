from __future__ import annotations

import pygame

from csp.graphics import CELL_SIZE, COLORS, COLS, ROWS, SCREEN_SIZE
from csp.state import State, all_entities


def draw_grid(screen: pygame.Surface) -> None:
    for x in range(0, COLS * CELL_SIZE, CELL_SIZE):
        pygame.draw.line(screen, COLORS["grid"], (x, 0), (x, ROWS * CELL_SIZE))
    for y in range(0, ROWS * CELL_SIZE, CELL_SIZE):
        pygame.draw.line(screen, COLORS["grid"], (0, y), (COLS * CELL_SIZE, y))


def draw_ui(state: State, screen: pygame.Surface, font: pygame.font.Font) -> None:
    panel_x = COLS * CELL_SIZE + 10
    stats = [
        f"Gold: {state.player.gold}",
        f"Meat: {state.player.meat}",
        f"Health: {state.player.health}",
        f"Turn: {state.turn_count}",
        "-------",
        "[H] Help",
        "[P] Punch",
        "[S] Shop/Talk",
        "[L] Labels",
        "[Space] Interact",
        "Use items [1..9,0]",
    ]
    # Draw stats
    for i, text in enumerate(stats):
        screen.blit(font.render(text, True, COLORS["text"]), (panel_x, 10 + i * 20))

    # Draw message log
    offset = 240
    for i, msg in enumerate(state.message_log):
        screen.blit(font.render(msg, True, COLORS["text"]), (panel_x, offset + i * 20))


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
    screen.fill(COLORS["background"])

    # Draw walls
    for wall in state.world.walls:
        pygame.draw.rect(
            screen,
            COLORS["wall"],
            (wall[0] * CELL_SIZE, wall[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE),
        )

    # Draw entities (non-player first)
    for e in all_entities(state):
        if e is state.player:
            continue
        pygame.draw.circle(
            screen,
            e.color,
            (
                e.x * CELL_SIZE + CELL_SIZE // 2,
                e.y * CELL_SIZE + CELL_SIZE // 2,
            ),
            CELL_SIZE // 2,
        )
        if state.show_labels:
            label = f"{e.name}"
            lbl_surf = font.render(label, True, (255, 255, 255))
            screen.blit(lbl_surf, (e.x * CELL_SIZE, e.y * CELL_SIZE - 10))

    # Draw player last
    pygame.draw.circle(
        screen,
        COLORS["player"],
        (
            state.player.x * CELL_SIZE + CELL_SIZE // 2,
            state.player.y * CELL_SIZE + CELL_SIZE // 2,
        ),
        CELL_SIZE // 2,
    )
    if state.show_labels:
        label = f"{state.player.name}"
        lbl_surf = font.render(label, True, (255, 255, 255))
        screen.blit(lbl_surf, (state.player.x * CELL_SIZE, state.player.y * CELL_SIZE - 10))

    # Grid + UI
    draw_grid(screen)
    draw_ui(state, screen, font)
    if state.show_help:
        draw_help(screen, font)
