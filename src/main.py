"""
Roguelike

Features:
- Random Dungeon: 30% randomly placed walls create a dynamic layout.
- Player Movement: Grid-based, with collision detection.
- Enemy AI: Ranging from random wanderers to basic chasers and wall-phasing threats.
- Bunny Hut: Spawns bunnies that can be punched for meat.
- Trapper NPC: Buys your collected meat for gold (access via 'S').
- Item Shop: Sells gear (Sword, Bow). These are inventory items used with hotkeys.
- Basic Combat: Punch with 'P' or use Sword (1) / Bow (2) if owned.
- UI Panels: Shows stats (gold, meat, health, turn) and recent messages.
- Help & Labels: Toggleable (H, L) overlays for instructions and on-screen entity names.
- Sound Effects: Punch, Sword, Bow, spawn, trader, purchase, etc., to enrich gameplay feedback.
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
        self.inventory = {}  # Can store 'gold','meat', or items like 'Sword','Bow'


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
        self.gold = 100
        self.meat = 0
        # Basic punch remains
        self.actions = {"punch": {"damage": 1, "range": 1}}
        self.inventory = {"gold": 0, "meat": 0}  # gold, meat, plus potential items.


class World:
    def __init__(self):
        self.grid = [[None for _ in range(ROWS)] for _ in range(COLS)]
        self.walls = set()
        self.generate_dungeon()
        self.spawn_entities()

    def generate_dungeon(self):
        # Simple random dungeon: 30% chance of wall
        for x in range(COLS):
            for y in range(ROWS):
                if random.random() < 0.3 and (x, y) != (COLS // 2, ROWS // 2):
                    self.walls.add((x, y))

    def spawn_entities(self):
        # Trapper
        self.trapper = Entity(
            5,
            5,
            "T",
            COLORS["trapper"],
            "Old Trapper",
            "Trades meat for gold",
            behavior="trader",
        )
        # Bunny Hut
        self.bunny_hut = Entity(
            COLS - 5,
            ROWS - 5,
            "H",
            COLORS["bunny_hut"],
            "Bunny Hut",
            "Spawns delicious friends",
            behavior="hut",
        )
        # Item Shop
        self.item_shop = Entity(
            COLS // 2,
            3,
            "I",
            COLORS["shop"],
            "Item Shop",
            "Sells powerful gear",
            behavior="shop",
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

        # Extra toggles
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
        self.sounds = {
            "punch": pygame.mixer.Sound("sounds/punch.mp3"),
            "sword": pygame.mixer.Sound("sounds/sword.mp3"),
            "bow": pygame.mixer.Sound("sounds/bow.mp3"),
            "grunt": pygame.mixer.Sound("sounds/grunt.mp3"),
        }

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
            self.player,
        ]

    # --- Core Gameplay Functions ---
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
                # Ignores walls and collision
                enemy.x = (enemy.x + random.choice([-1, 1])) % COLS
                enemy.y = (enemy.y + random.choice([-1, 1])) % ROWS

    def handle_combat(self):
        """Basic punch with 'P' key."""
        dmg = self.player.actions["punch"]["damage"]
        rng = self.player.actions["punch"]["range"]
        self.perform_attack("Punch", dmg, rng, "punch")

    def perform_attack(self, attack_name, dmg, rng, sound_key):
        """Handles the common logic of attacking with given damage and range."""
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

    def update_economy(self):
        # 5% chance per turn to spawn bunny near the hut
        if random.random() < 0.05:
            self.spawn_bunny()

    # --- Commerce / Shop ---
    def handle_commerce(self):
        """Check if we're next to the trapper or the item shop, and interact accordingly."""
        if is_adjacent(self.player, self.world.trapper):
            self.trade_with_trapper()
        elif is_adjacent(self.player, self.world.item_shop):
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
        """Attempt to buy any items if we have enough gold."""
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
            "[L] Labels On/Off",
            "Use items with [1..9,0]",
        ]
        # Draw stats
        for i, text in enumerate(stats):
            self.screen.blit(
                self.font.render(text, True, COLORS["text"]), (panel_x, 10 + i * 20)
            )

        # Draw message log
        offset = 200
        for i, msg in enumerate(self.message_log):
            self.screen.blit(
                self.font.render(msg, True, COLORS["text"]), (panel_x, offset + i * 20)
            )

    def draw_help(self):
        help_text = [
            "Controls:",
            "Arrow Keys: Move",
            "H: Toggle Help",
            "P: Punch (adjacent target)",
            "S: Shop/Talk (trapper or item shop)",
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

            # Draw entities (enemies, trapper, huts, shops, etc.)
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

            # Draw player last on top
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
                        # Basic punch
                        self.handle_combat()

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

                    elif event.key == pygame.K_s:
                        self.handle_commerce()

                    # Item usage hotkeys
                    elif event.key == pygame.K_1:
                        self.use_item("Sword")
                    elif event.key == pygame.K_2:
                        self.use_item("Bow")
                    # You can expand 3..0 similarly if you add more items.

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = RogueLike()
    game.run()
