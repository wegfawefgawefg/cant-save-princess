"""
Roguelike

Features:
- Random Dungeon with a blocked-off 30x30 temple maze in the bottom-left.
- Chest in the temple center. Interact (Space) to get 10,000 gold.
- Bunny Hut area (bottom-right) is kept clear (10x10) so the player can enter easily.
- Player Movement, Enemy AI, Shop/Trapper interactions, and Sword/Bow usage remain the same.
"""

import pygame
import random
from enum import Enum
from collections import deque

# Game Constants
CELL_SIZE = 15
COLS, ROWS = 60, 40  # 900x600 play area
PANEL_WIDTH = 300
SCREEN_SIZE = (COLS * CELL_SIZE + PANEL_WIDTH, ROWS * CELL_SIZE)
FPS = 60

# Colors
COLORS = {
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


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


def is_adjacent(a, b):
    return abs(a.x - b.x) <= 1 and abs(a.y - b.y) <= 1


class Entity:
    def __init__(self, x, y, char, color, name, description, behavior=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.description = description
        self.behavior = behavior
        self.health = 3
        self.inventory = {}  # e.g. 'gold','meat','Sword','Bow'...
        # For special items/entities
        self.opened = False  # e.g. for chest


class Player(Entity):
    def __init__(self):
        super().__init__(
            COLS // 2,
            ROWS // 2,
            "@",
            COLORS["player"],
            "The Chrono Exile",
            "Bearer of temporal shards",
        )
        self.health = 20
        self.gold = 0
        self.meat = 0
        # Basic punch remains
        self.actions = {"punch": {"damage": 1, "range": 1}}
        self.inventory = {"gold": 0, "meat": 0}


class World:
    def __init__(self):
        self.grid = [[None for _ in range(ROWS)] for _ in range(COLS)]
        self.walls = set()
        self.bunny_hut = None
        self.trapper = None
        self.item_shop = None
        self.chest = None

        self.generate_dungeon()
        self.spawn_entities()

    def generate_dungeon(self):
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
                in_maze_region = (maze_left <= x < maze_right) and (
                    maze_top <= y < maze_bottom
                )

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
        entrance_y = maze_top - 1  # just outside the region
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
        self.chest_position = (chest_x, chest_y)

    def spawn_entities(self):
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


class RogueLike:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.font = pygame.font.SysFont("Courier", 14)
        self.clock = pygame.time.Clock()
        self.world = World()
        self.player = Player()
        self.enemies = self.create_enemies()
        self.turn_count = 0

        # Toggles
        self.show_help = False
        self.show_labels = False

        # Basic in-game messages
        self.message_log = deque(maxlen=10)

        # Possible shop items
        self.shop_items = [
            {
                "name": "Sword",
                "cost": 5,
                "desc": "Adds a sword to inventory (press 1 to use).",
            },
            {
                "name": "Bow",
                "cost": 8,
                "desc": "Adds a bow to inventory (press 2 to use).",
            },
        ]

        # Load sounds (place actual .wav/.mp3 files in a "sounds" folder)
        self.sounds = {}
        try:
            self.sounds = {
                "punch": pygame.mixer.Sound("sounds/punch.mp3"),
                "sword": pygame.mixer.Sound("sounds/sword.mp3"),
                "bow": pygame.mixer.Sound("sounds/bow.mp3"),
            }
        except:
            print("Sounds not loaded. Check files...")

    def create_enemies(self):
        return [
            Entity(
                10,
                10,
                "S",
                (120, 80, 200),
                "Shardling Slime",
                "Seeps through cracks",
                behavior="random",
            ),
            Entity(
                15,
                15,
                "B",
                (200, 60, 60),
                "Bloodsteel Bandit",
                "Hunts the living",
                behavior="chase",
            ),
            Entity(
                20,
                20,
                "G",
                (160, 30, 160),
                "Gloom Specter",
                "Phases through walls",
                behavior="phase",
            ),
        ]

    def all_entities(self):
        """Helper to get a list of all game entities."""
        return self.enemies + [
            self.world.trapper,
            self.world.bunny_hut,
            self.world.item_shop,
            self.world.chest,
            self.player,
        ]

    # --- Core Gameplay ---
    def can_move_to(self, x, y, ignore_entity=None):
        """Checks walls and other entities for collision."""
        if not (0 <= x < COLS and 0 <= y < ROWS):
            return False
        if (x, y) in self.world.walls:
            return False
        # Check if another entity occupies that space
        for e in self.all_entities():
            if e is ignore_entity:
                continue
            if (e.x, e.y) == (x, y):
                return False
        return True

    def move_entity(self, entity, dx, dy):
        new_x = entity.x + dx
        new_y = entity.y + dy
        if self.can_move_to(new_x, new_y, ignore_entity=entity):
            entity.x = new_x
            entity.y = new_y
            return True
        return False

    def enemy_ai(self):
        for enemy in self.enemies:
            if enemy.behavior == "random":
                dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                self.move_entity(enemy, dx, dy)
            elif enemy.behavior == "chase":
                dx = 1 if self.player.x > enemy.x else -1
                dy = 1 if self.player.y > enemy.y else -1
                # Move in x direction first
                if not self.move_entity(enemy, dx, 0):
                    self.move_entity(enemy, 0, dy)
            elif enemy.behavior == "phase":
                # Ignores walls entirely
                enemy.x = (enemy.x + random.choice([-1, 1])) % COLS
                enemy.y = (enemy.y + random.choice([-1, 1])) % ROWS

    # --- Combat ---
    def handle_combat(self):
        """Basic punch with 'P' key."""
        dmg = self.player.actions["punch"]["damage"]
        rng = self.player.actions["punch"]["range"]
        self.perform_attack("Punch", dmg, rng, "punch")

    def perform_attack(self, attack_name, dmg, rng, sound_key):
        targets = []
        for e in self.enemies:
            if abs(e.x - self.player.x) <= rng and abs(e.y - self.player.y) <= rng:
                targets.append(e)
        if targets:
            target = targets[0]
            target.health -= dmg
            # Play relevant sound
            if sound_key in self.sounds:
                self.sounds[sound_key].play()
            self.message_log.append(
                f"You used {attack_name} on {target.name} for {dmg} damage!"
            )
            if target.health <= 0:
                self.message_log.append(f"You killed the {target.name}!")
                if target.name == "Bunny":
                    self.player.meat += 1
                    self.message_log.append("You collected 1 meat.")
                self.enemies.remove(target)
        else:
            self.message_log.append(f"No target in range for {attack_name}.")

    # --- Economy / Bunnies ---
    def update_economy(self):
        # 5% chance per turn to spawn bunny near the hut
        if random.random() < 0.05:
            self.spawn_bunny()

    def spawn_bunny(self):
        hut = self.world.bunny_hut
        # Try a few random spots near the hut
        for _ in range(10):
            x = hut.x + random.randint(-2, 2)
            y = hut.y + random.randint(-2, 2)
            if self.can_move_to(x, y):
                bunny = Entity(
                    x,
                    y,
                    "b",
                    COLORS["bunny"],
                    "Bunny",
                    "Harmless fluff",
                    behavior="random",
                )
                bunny.health = 1
                self.enemies.append(bunny)
                break

    # --- Commerce / Shop ---
    def handle_commerce(self):
        """Check adjacency to trapper/shop, then open relevant menu."""
        trapper = self.world.trapper
        shop = self.world.item_shop
        if is_adjacent(self.player, trapper):
            self.trade_with_trapper()
        elif is_adjacent(self.player, shop):
            self.open_item_shop()
        else:
            self.message_log.append("Not near any vendor.")

    def trade_with_trapper(self):
        """Trade all meat 1:1 for gold."""
        if self.player.meat > 0:
            amt = self.player.meat
            self.player.gold += amt
            self.player.meat = 0
            self.message_log.append(f"Traded {amt} meat for {amt} gold.")
        else:
            self.message_log.append("You have no meat to trade.")

    def open_item_shop(self):
        """Attempt to buy items if you have enough gold."""
        for item in self.shop_items:
            cost = item["cost"]
            name = item["name"]
            if self.player.gold >= cost:
                self.player.gold -= cost
                self.message_log.append(f"You bought a {name}!")
                # Add item to inventory
                self.player.inventory[name] = True
            else:
                self.message_log.append(f"Not enough gold for {name} ({cost}g).")

    # --- Item usage ---
    def use_item(self, item_name):
        """Use an item from inventory. Sword=damage3 range1, Bow=damage2 range2."""
        if item_name not in self.player.inventory:
            self.message_log.append(f"You don't have a {item_name}.")
            return

        if item_name == "Sword":
            self.perform_attack("Sword Slash", 3, 1, "sword")
        elif item_name == "Bow":
            self.perform_attack("Bow Shot", 2, 2, "bow")

    # --- Interactables (Space Key) ---
    def handle_interact(self):
        """For things like the Chest. If adjacent, open it."""
        for e in self.all_entities():
            if e.behavior == "chest" and not e.opened:
                # if adjacent to the chest
                if is_adjacent(self.player, e):
                    e.opened = True
                    self.player.gold += 10000
                    self.message_log.append(
                        "You opened the chest and found 10,000 gold!"
                    )
                    # Change chest icon to something else to indicate 'opened'
                    e.char = "o"
                    e.color = (180, 180, 90)
                    return
        self.message_log.append("Nothing here to interact with.")

    # --- UI Rendering ---
    def draw_grid(self):
        for x in range(0, COLS * CELL_SIZE, CELL_SIZE):
            pygame.draw.line(self.screen, COLORS["grid"], (x, 0), (x, ROWS * CELL_SIZE))
        for y in range(0, ROWS * CELL_SIZE, CELL_SIZE):
            pygame.draw.line(self.screen, COLORS["grid"], (0, y), (COLS * CELL_SIZE, y))

    def draw_ui(self):
        panel_x = COLS * CELL_SIZE + 10
        stats = [
            f"Gold: {self.player.gold}",
            f"Meat: {self.player.meat}",
            f"Health: {self.player.health}",
            f"Turn: {self.turn_count}",
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
            self.screen.blit(
                self.font.render(text, True, COLORS["text"]), (panel_x, 10 + i * 20)
            )

        # Draw message log
        offset = 240
        for i, msg in enumerate(self.message_log):
            self.screen.blit(
                self.font.render(msg, True, COLORS["text"]), (panel_x, offset + i * 20)
            )

    def draw_help(self):
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
        # Draw a semi-transparent rectangle
        overlay = pygame.Surface((SCREEN_SIZE[0], SCREEN_SIZE[1]))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        # Draw help text
        for i, line in enumerate(help_text):
            self.screen.blit(
                self.font.render(line, True, COLORS["text"]), (50, 50 + i * 20)
            )

    def run(self):
        running = True
        while running:
            self.screen.fill(COLORS["background"])

            # Draw walls
            for wall in self.world.walls:
                pygame.draw.rect(
                    self.screen,
                    COLORS["wall"],
                    (wall[0] * CELL_SIZE, wall[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE),
                )

            # Draw entities
            for e in self.all_entities():
                if e is self.player:
                    continue  # skip player for now
                pygame.draw.circle(
                    self.screen,
                    e.color,
                    (
                        e.x * CELL_SIZE + CELL_SIZE // 2,
                        e.y * CELL_SIZE + CELL_SIZE // 2,
                    ),
                    CELL_SIZE // 2,
                )
                # If labeling is on
                if self.show_labels:
                    label = f"{e.name}"
                    lbl_surf = self.font.render(label, True, (255, 255, 255))
                    self.screen.blit(lbl_surf, (e.x * CELL_SIZE, e.y * CELL_SIZE - 10))

            # Draw player last
            pygame.draw.circle(
                self.screen,
                COLORS["player"],
                (
                    self.player.x * CELL_SIZE + CELL_SIZE // 2,
                    self.player.y * CELL_SIZE + CELL_SIZE // 2,
                ),
                CELL_SIZE // 2,
            )
            if self.show_labels:
                label = f"{self.player.name}"
                lbl_surf = self.font.render(label, True, (255, 255, 255))
                self.screen.blit(
                    lbl_surf,
                    (self.player.x * CELL_SIZE, self.player.y * CELL_SIZE - 10),
                )

            # Grid + UI
            self.draw_grid()
            self.draw_ui()
            if self.show_help:
                self.draw_help()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_h:
                        self.show_help = not self.show_help
                    elif event.key == pygame.K_l:
                        self.show_labels = not self.show_labels
                    elif event.key == pygame.K_p:
                        self.handle_combat()
                    elif event.key == pygame.K_s:
                        self.handle_commerce()
                    elif event.key == pygame.K_SPACE:
                        self.handle_interact()

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
                        if self.move_entity(self.player, dx, dy):
                            self.turn_count += 1
                            self.enemy_ai()
                            self.update_economy()

                    # Item usage hotkeys
                    elif event.key == pygame.K_1:
                        self.use_item("Sword")
                    elif event.key == pygame.K_2:
                        self.use_item("Bow")
                    # expand 3..9,0 as needed

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = RogueLike()
    game.run()
