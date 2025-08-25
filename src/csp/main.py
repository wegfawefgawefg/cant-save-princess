"""
Roguelike entrypoint for the refactored, de-OOPed architecture.
"""

import pygame

from csp.graphics import Graphics
from csp.map_runtime import load_map
from csp.state import State
from csp.step import step_loop


def main() -> None:
    pygame.init()
    gfx = Graphics.create()
    state = State()
    # Load initial area; spawn slightly below center so we don't cover the sign
    start = state.maps["start_area"].size
    spawn = (start[0] // 2, min(start[1] - 2, start[1] // 2 + 2))
    load_map(state, "start_area", spawn_pos=spawn)
    step_loop(state, gfx.screen, gfx.font)


if __name__ == "__main__":
    main()
