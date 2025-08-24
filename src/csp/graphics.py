from __future__ import annotations

from dataclasses import dataclass

import pygame

# Graphics-related configuration
CELL_SIZE: int = 15
COLS: int = 60
ROWS: int = 40  # 900x600 play area
PANEL_WIDTH: int = 300
SCREEN_SIZE: tuple[int, int] = (COLS * CELL_SIZE + PANEL_WIDTH, ROWS * CELL_SIZE)
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
        screen = pygame.display.set_mode(SCREEN_SIZE)
        font = pygame.font.SysFont("Courier", 14)
        return Graphics(screen=screen, font=font)
