from __future__ import annotations

import random

from csp.entities import Entity
from csp.graphics import COLORS, COLS, ROWS


class World:
    def __init__(self) -> None:
        self.grid: list[list[object | None]] = [[None for _ in range(ROWS)] for _ in range(COLS)]
        self.walls: set[tuple[int, int]] = set()
        self.bunny_hut: Entity | None = None
        self.trapper: Entity | None = None
        self.item_shop: Entity | None = None
        self.chest: Entity | None = None

        self.generate_dungeon()
        self.spawn_entities()

    def generate_dungeon(self) -> None:
        """
        1) Start with random walls.
        2) Make a 10x10 clear area in bottom-right for the Bunny Hut.
        3) Make a 30x30 'temple maze' in bottom-left with one entrance.
        4) Place a chest at the center of that maze.
        """

        # 1) Random fill except we'll skip:
        #    - The bottom-right 10x10 region.
        #    - The bottom-left 30x30 region (we'll fill it separately with our custom maze).
        for x in range(COLS):
            for y in range(ROWS):
                # Define the bottom-right clear area
                clear_br_left = COLS - 10
                clear_br_top = ROWS - 10
                # Define the bottom-left maze region
                maze_left = 0
                maze_right = 30
                maze_top = ROWS - 30  # i.e. 40 - 30 = 10
                maze_bottom = ROWS

                in_bunny_area = (x >= clear_br_left) and (y >= clear_br_top)
                in_maze_region = (maze_left <= x < maze_right) and (maze_top <= y < maze_bottom)

                if in_bunny_area:
                    # Force no walls in bottom-right 10x10
                    continue
                elif in_maze_region:
                    # We'll carve it out later
                    continue
                else:
                    # 30% random chance
                    if random.random() < 0.3 and (x, y) != (COLS // 2, ROWS // 2):
                        self.walls.add((x, y))

        # 2) Carve a small maze in the bottom-left 30x30 region
        #    We'll fill that region fully with walls first, then carve paths.
        maze_left = 0
        maze_right = 30
        maze_top = ROWS - 30  # 10
        maze_bottom = ROWS  # 40

        # Fill region with walls
        for x in range(maze_left, maze_right):
            for y in range(maze_top, maze_bottom):
                self.walls.add((x, y))

        # We'll do a simple "drunken walk" to carve out some corridors.
        # You can customize this if you want more complex labyrinths.
        # Start near the single entrance:
        entrance_x = 15  # the single entrance horizontally
        # We'll open one tile at the actual entrance
        if (entrance_x, maze_top) in self.walls:
            self.walls.remove((entrance_x, maze_top))

        # Carve random walk from that entrance area
        carve_x = entrance_x
        carve_y = maze_top

        steps = 300  # arbitrary number of random steps
        for _ in range(steps):
            # Make sure we remove the wall at the current position
            if (carve_x, carve_y) in self.walls:
                self.walls.remove((carve_x, carve_y))

            # Random direction
            dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            nx = carve_x + dx
            ny = carve_y + dy
            # Keep within maze region
            if maze_left <= nx < maze_right and maze_top <= ny < maze_bottom:
                carve_x, carve_y = nx, ny

        # 3) We'll place the chest in the approximate center
        chest_x = (maze_left + maze_right) // 2  # ~15
        chest_y = (maze_top + maze_bottom) // 2  # ~25
        # Make sure it's not a wall
        if (chest_x, chest_y) in self.walls:
            self.walls.remove((chest_x, chest_y))

        # We'll create the chest entity in spawn_entities
        self.chest_position: tuple[int, int] = (chest_x, chest_y)

    def spawn_entities(self) -> None:
        # (a) Trapper
        self.trapper = Entity(
            5,
            5,
            "T",
            COLORS["trapper"],
            "Old Trapper",
            "Trades meat for gold",
            behavior="trader",
        )
        # (b) Bunny Hut in bottom-right
        hut_x = COLS - 5
        hut_y = ROWS - 5
        self.bunny_hut = Entity(
            hut_x,
            hut_y,
            "H",
            COLORS["bunny_hut"],
            "Bunny Hut",
            "Spawns delicious friends",
            behavior="hut",
        )
        # (c) Item Shop
        self.item_shop = Entity(
            COLS // 2,
            3,
            "I",
            COLORS["shop"],
            "Item Shop",
            "Sells powerful gear",
            behavior="shop",
        )
        # (d) Chest in the maze center
        cx, cy = self.chest_position
        self.chest = Entity(
            cx,
            cy,
            "C",
            COLORS["chest"],
            "Treasure Chest",
            "Might contain a legendary sum!",
            behavior="chest",
        )
