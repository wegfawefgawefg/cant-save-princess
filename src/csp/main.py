"""
Roguelike entrypoint for the refactored, de-OOPed architecture.
"""

import pygame

from csp.graphics import Graphics
from csp.state import State
from csp.step import step_loop


def main() -> None:
    pygame.init()
    gfx = Graphics.create()
    state = State()
    step_loop(state, gfx.screen, gfx.font)


if __name__ == "__main__":
    main()
