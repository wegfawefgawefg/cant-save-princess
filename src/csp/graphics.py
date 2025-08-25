from __future__ import annotations

from dataclasses import dataclass

import pygame

# Graphics-related configuration
CELL_SIZE: int = 15
# Viewport size (tiles) rendered in the central play area; keep 16:9
COLS: int = 64  # 64 * 15 = 960
ROWS: int = 36  # 36 * 15 = 540  => 960x540 (16:9)
PANEL_WIDTH: int = 300
LEFT_PANEL_WIDTH: int = 150
GAME_OFFSET_X: int = LEFT_PANEL_WIDTH
SCREEN_SIZE: tuple[int, int] = (
    LEFT_PANEL_WIDTH + COLS * CELL_SIZE + PANEL_WIDTH,
    ROWS * CELL_SIZE,
)
FULLSCREEN: bool = False
FPS: int = 60

# Colors
COLORS: dict[str, tuple[int, int, int]] = {
    "background": (25, 25, 30),
    "grid": (40, 40, 50),
    "player": (200, 220, 255),
    "text": (220, 220, 220),
    "wall": (80, 80, 100),
    "gold": (255, 215, 0),
    "meat": (200, 60, 40),
    "shop": (70, 200, 70),
    "trapper": (150, 75, 0),
    "bunny_hut": (200, 150, 100),
    "bunny": (240, 240, 240),
    "chest": (255, 215, 0),
}


@dataclass
class Graphics:
    screen: pygame.Surface
    font: pygame.font.Font

    @staticmethod
    def create() -> Graphics:
        flags = pygame.FULLSCREEN if FULLSCREEN else 0
        screen = pygame.display.set_mode(SCREEN_SIZE, flags)
        font = pygame.font.SysFont("Courier", 14)
        return Graphics(screen=screen, font=font)
