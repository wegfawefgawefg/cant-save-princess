from __future__ import annotations

import pygame

from csp.ai import enemy_ai
from csp.combat import handle_combat
from csp.commerce import handle_commerce
from csp.common import Direction
from csp.draw import draw_frame
from csp.economy import update_economy
from csp.graphics import FPS
from csp.interact import handle_interact
from csp.items import use_item
from csp.movement import move_entity
from csp.state import State


def step_loop(state: State, screen, font) -> None:
    clock = state.clock
    running = True
    while running:
        draw_frame(state, screen, font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    state.show_help = not state.show_help
                elif event.key == pygame.K_l:
                    state.show_labels = not state.show_labels
                elif event.key == pygame.K_p:
                    handle_combat(state)
                elif event.key == pygame.K_s:
                    handle_commerce(state)
                elif event.key == pygame.K_SPACE:
                    handle_interact(state)

                elif event.key in (
                    pygame.K_UP,
                    pygame.K_DOWN,
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                ):
                    dir_map = {
                        pygame.K_UP: Direction.UP,
                        pygame.K_DOWN: Direction.DOWN,
                        pygame.K_LEFT: Direction.LEFT,
                        pygame.K_RIGHT: Direction.RIGHT,
                    }
                    dx, dy = dir_map[event.key].value
                    if move_entity(state, state.player, dx, dy):
                        state.turn_count += 1
                        enemy_ai(state)
                        update_economy(state)

                # Item usage hotkeys
                elif event.key == pygame.K_1:
                    use_item(state, "Sword")
                elif event.key == pygame.K_2:
                    use_item(state, "Bow")

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
