from __future__ import annotations

import pygame

from csp.actions import perform_dialogue_action
from csp.ai import enemy_ai
from csp.combat import handle_combat
from csp.common import Direction
from csp.draw import (
    draw_dialogue,
    draw_frame,
    draw_inventory_menu,
    draw_main_menu,
    draw_settings_menu,
    draw_shop_menu,
)
from csp.economy import update_economy
from csp.flags import tick_flags, has_flag
from csp.graphics import FPS
from csp.interact import handle_interact
from csp.items import use_item
from csp.map_runtime import check_warp_after_move
from csp.map_runtime import process_triggers_after_move
from csp.messages import log
from csp.movement import move_entity
from csp.state import GameMode, State


def _play_sound(state: State, key: str) -> None:
    s = state.sounds.get(key)
    if s is not None:
        try:
            s.play()
        except Exception:
            pass


def _do_player_move(state: State, direction: Direction) -> None:
    dx, dy = direction.value

    if move_entity(state, state.player, dx, dy):
        state.turn_count += 1
        process_triggers_after_move(state)
        enemy_ai(state)
        update_economy(state)
        check_warp_after_move(state, direction)
        tick_flags(state)
        # Handle per-item timed effects (e.g., torch burn) after flags tick
        try:
            from csp.items import tick_items_per_turn

            tick_items_per_turn(state)
        except Exception:
            pass
        state.move_repeat_last_time_ms = pygame.time.get_ticks()
        state.move_repeat_last_dir = direction.value


def process_inputs_playing(state: State, event: pygame.event.Event) -> None:
    if event.type != pygame.KEYDOWN:
        return
    if event.key == pygame.K_h:
        state.show_help = not state.show_help
    elif event.key == pygame.K_l:
        state.show_labels = not state.show_labels
    elif event.key == pygame.K_i:
        state.menu_inventory_index = 0
        state.mode = GameMode.INVENTORY
    elif event.key == pygame.K_p:
        handle_combat(state)
    elif event.key == pygame.K_SPACE:
        # Interact can handle talk/shop/sign/switch/door; allow direction to break ties
        pressed = pygame.key.get_pressed()
        preferred: Direction | None = None
        if pressed[pygame.K_UP]:
            preferred = Direction.UP
        elif pressed[pygame.K_DOWN]:
            preferred = Direction.DOWN
        elif pressed[pygame.K_LEFT]:
            preferred = Direction.LEFT
        elif pressed[pygame.K_RIGHT]:
            preferred = Direction.RIGHT
        if preferred is None:
            preferred = state.last_dir_key
        handle_interact(state, preferred)
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
        state.last_dir_key = dir_map[event.key]
        _do_player_move(state, dir_map[event.key])
    elif event.key in (
        pygame.K_1,
        pygame.K_2,
        pygame.K_3,
        pygame.K_4,
        pygame.K_5,
        pygame.K_6,
        pygame.K_7,
        pygame.K_8,
        pygame.K_9,
        pygame.K_0,
    ):
        key_map = {
            pygame.K_1: "1",
            pygame.K_2: "2",
            pygame.K_3: "3",
            pygame.K_4: "4",
            pygame.K_5: "5",
            pygame.K_6: "6",
            pygame.K_7: "7",
            pygame.K_8: "8",
            pygame.K_9: "9",
            pygame.K_0: "0",
        }
        slot = key_map[event.key]
        item = state.binds.get(slot)
        if item:
            use_item(state, item)


def process_inputs_main_menu(state: State, event: pygame.event.Event) -> bool:
    """Returns True if should quit the game."""
    if event.type != pygame.KEYDOWN:
        return False
    options_len = 3  # Play, Settings, Quit
    if event.key == pygame.K_UP:
        prev = state.menu_main_index
        state.menu_main_index = (state.menu_main_index - 1) % options_len
        if state.menu_main_index != prev:
            _play_sound(state, "bow")
    elif event.key == pygame.K_DOWN:
        prev = state.menu_main_index
        state.menu_main_index = (state.menu_main_index + 1) % options_len
        if state.menu_main_index != prev:
            _play_sound(state, "bow")
    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
        _play_sound(state, "punch")
        if state.menu_main_index == 0:  # Play
            state.mode = GameMode.PLAYING
        elif state.menu_main_index == 1:  # Settings
            state.mode = GameMode.SETTINGS
        else:  # Quit
            return True
    elif event.key == pygame.K_ESCAPE:
        # ESC does nothing on main menu (no back target)
        pass
    return False


def process_inputs_settings(state: State, event: pygame.event.Event) -> None:
    if event.type != pygame.KEYDOWN:
        return
    options_len = 1  # Back only
    if event.key in (pygame.K_UP, pygame.K_DOWN):
        # Only one option, but still play move sound when pressing nav keys
        _play_sound(state, "bow")
    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
        _play_sound(state, "punch")
        state.mode = GameMode.MAIN_MENU


def process_inputs_shop(state: State, event: pygame.event.Event) -> None:
    if event.type != pygame.KEYDOWN:
        return
    items = state.shop_inventories.get(state.active_shop_id or "", [])
    if not items:
        return
    if event.key == pygame.K_UP:
        prev = state.menu_shop_index
        state.menu_shop_index = (state.menu_shop_index - 1) % len(items)
        if state.menu_shop_index != prev:
            _play_sound(state, "bow")
    elif event.key == pygame.K_DOWN:
        prev = state.menu_shop_index
        state.menu_shop_index = (state.menu_shop_index + 1) % len(items)
        if state.menu_shop_index != prev:
            _play_sound(state, "bow")
    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
        it = items[state.menu_shop_index]
        name = it["name"]
        cost = it["cost"]
        max_qty = it["max_qty"]
        purchased = it.get("purchased", 0)
        if (max_qty is not None) and (purchased >= max_qty):
            log(state, f"{name} is sold out.")
            _play_sound(state, "grunt")
            return
        if state.player.gold < cost:
            log(state, f"Not enough gold for {name} ({cost}g).")
            _play_sound(state, "grunt")
            return
        state.player.gold -= cost
        it["purchased"] = purchased + 1
        state.owned_items[name] = state.owned_items.get(name, 0) + 1
        # Ensure compatibility with use_item
        state.player.inventory[name] = True
        log(state, f"You bought a {name}!")
        _play_sound(state, "punch")
    elif event.key == pygame.K_ESCAPE:
        # Back to playing
        state.mode = GameMode.PLAYING


def process_inputs_inventory(state: State, event: pygame.event.Event) -> None:
    if event.type != pygame.KEYDOWN:
        return
    items = sorted(state.owned_items.keys())
    # Allow back-out even with no items
    if event.key == pygame.K_UP:
        if not items:
            return
        prev = state.menu_inventory_index
        state.menu_inventory_index = (state.menu_inventory_index - 1) % len(items)
        if state.menu_inventory_index != prev:
            _play_sound(state, "bow")
    elif event.key == pygame.K_DOWN:
        if not items:
            return
        prev = state.menu_inventory_index
        state.menu_inventory_index = (state.menu_inventory_index + 1) % len(items)
        if state.menu_inventory_index != prev:
            _play_sound(state, "bow")
    elif event.key in (
        pygame.K_1,
        pygame.K_2,
        pygame.K_3,
        pygame.K_4,
        pygame.K_5,
        pygame.K_6,
        pygame.K_7,
        pygame.K_8,
        pygame.K_9,
        pygame.K_0,
    ):
        if not items:
            return
        key_map = {
            pygame.K_1: "1",
            pygame.K_2: "2",
            pygame.K_3: "3",
            pygame.K_4: "4",
            pygame.K_5: "5",
            pygame.K_6: "6",
            pygame.K_7: "7",
            pygame.K_8: "8",
            pygame.K_9: "9",
            pygame.K_0: "0",
        }
        slot = key_map[event.key]
        item = items[state.menu_inventory_index]
        state.binds[slot] = item
        log(state, f"Bound {item} to [{slot}].")
        _play_sound(state, "punch")
    elif event.key in (pygame.K_ESCAPE, pygame.K_i):
        # If the player is dead, return to DEAD screen; otherwise back to playing
        state.mode = GameMode.PLAYING if state.player.health > 0 else GameMode.DEAD


def process_inputs_dead(state: State, event: pygame.event.Event) -> None:
    if event.type != pygame.KEYDOWN:
        return
    if event.key == pygame.K_i:
        state.menu_inventory_index = 0
        state.mode = GameMode.INVENTORY
    elif event.key == pygame.K_h:
        state.show_help = not state.show_help
    elif event.key == pygame.K_l:
        state.show_labels = not state.show_labels


def process_inputs_dialogue(state: State, event: pygame.event.Event) -> None:
    if event.type != pygame.KEYDOWN:
        return
    tree = state.dialogues.get(state.dialogue_id or "")
    if not tree:
        state.mode = GameMode.PLAYING
        return
    nodes = tree.get("nodes", {})
    node = nodes.get(state.dialogue_node or "")
    if not node:
        state.mode = GameMode.PLAYING
        return
    options = node.get("options", [])
    if event.key == pygame.K_UP:
        if options:
            state.menu_dialogue_index = (state.menu_dialogue_index - 1) % len(options)
            _play_sound(state, "bow")
    elif event.key == pygame.K_DOWN:
        if options:
            state.menu_dialogue_index = (state.menu_dialogue_index + 1) % len(options)
            _play_sound(state, "bow")
    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
        if options:
            opt = options[state.menu_dialogue_index]
            action = opt.get("action")
            if action:
                perform_dialogue_action(state, action)
            nxt = opt.get("next")
            if nxt:
                state.dialogue_node = nxt
                state.menu_dialogue_index = 0
                node2 = nodes.get(state.dialogue_node, {})
                if node2.get("end"):
                    state.mode = GameMode.PLAYING
    elif event.key == pygame.K_ESCAPE:
        if tree.get("backoutable", True):
            state.mode = GameMode.PLAYING


def step_loop(state: State, screen, font) -> None:
    clock = state.clock
    running = True
    while running:
        if state.mode == GameMode.MAIN_MENU:
            draw_main_menu(state, screen, font)
        elif state.mode == GameMode.SETTINGS:
            draw_settings_menu(state, screen, font)
        elif state.mode == GameMode.SHOP:
            draw_shop_menu(state, screen, font)
        elif state.mode == GameMode.INVENTORY:
            draw_inventory_menu(state, screen, font)
        elif state.mode == GameMode.DIALOGUE:
            draw_dialogue(state, screen, font)
        else:
            draw_frame(state, screen, font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif (
                event.type == pygame.KEYDOWN
                and (event.key == pygame.K_q)
                and (event.mod & pygame.KMOD_CTRL)
            ):
                # Dev-time super quit
                running = False
            else:
                if state.mode == GameMode.MAIN_MENU:
                    if process_inputs_main_menu(state, event):
                        running = False
                elif state.mode == GameMode.SETTINGS:
                    process_inputs_settings(state, event)
                elif state.mode == GameMode.SHOP:
                    process_inputs_shop(state, event)
                elif state.mode == GameMode.INVENTORY:
                    process_inputs_inventory(state, event)
                elif state.mode == GameMode.DIALOGUE:
                    process_inputs_dialogue(state, event)
                elif state.mode == GameMode.DEAD:
                    process_inputs_dead(state, event)
                else:
                    # Running toggle + message
                    if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_LCTRL,
                        pygame.K_RCTRL,
                    ):
                        if not state.run_active:
                            state.run_active = True
                            log(state, "Hero begins running.")
                    elif event.type == pygame.KEYUP and event.key in (
                        pygame.K_LCTRL,
                        pygame.K_RCTRL,
                    ):
                        if state.run_active:
                            state.run_active = False
                            log(state, "Hero stops running.")
                    process_inputs_playing(state, event)

        # Handle held-move repeat in PLAYING mode
        if state.mode == GameMode.PLAYING:
            pressed = pygame.key.get_pressed()
            dir_key: Direction | None = None
            if pressed[pygame.K_UP]:
                dir_key = Direction.UP
            elif pressed[pygame.K_DOWN]:
                dir_key = Direction.DOWN
            elif pressed[pygame.K_LEFT]:
                dir_key = Direction.LEFT
            elif pressed[pygame.K_RIGHT]:
                dir_key = Direction.RIGHT

            if dir_key is not None:
                now = pygame.time.get_ticks()
                interval = state.move_repeat_interval_ms
                if pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]:
                    interval = max(1, interval // 2)
                # If direction changed since last repeat, allow immediate move
                if state.move_repeat_last_dir != dir_key.value:
                    _do_player_move(state, dir_key)
                elif now - state.move_repeat_last_time_ms >= interval:
                    _do_player_move(state, dir_key)
            else:
                state.move_repeat_last_dir = None

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
