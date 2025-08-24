from enum import Enum


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


def is_adjacent(a, b):
    return abs(a.x - b.x) <= 1 and abs(a.y - b.y) <= 1
