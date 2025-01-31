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
