from __future__ import annotations

import random
from typing import Iterator, List, Tuple

import numpy as np
from tcod import libtcodpy

import ai
import fighter
import gamemap
import item

WALL = gamemap.Tile(
    move_cost=0,
    transparent=False,
    light=(ord("="), (106, 140, 219), (255, 226, 83)),
    dark=(ord("="), (106, 140, 219), (42, 65, 118)),
    memory=(ord("="), (64, 92, 157), (17, 31, 63)),
)
FLOOR = gamemap.Tile(
    move_cost=1,
    transparent=True,
    light=(ord(" "), (255, 255, 255), (243, 210, 52)),
    dark=(ord(" "), (255, 255, 255), (17, 31, 63)),
    memory=(ord(" "), (255, 255, 255), (4, 9, 19)),
)


class Room:
    """Holds data and methods used to generate rooms."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def outer(self) -> Tuple[slice, slice]:
        """Return the NumPy index for the whole room."""
        index: Tuple[slice, slice] = np.s_[self.x1 : self.x2, self.y1 : self.y2]
        return index

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the NumPy index for the inner room area."""
        index: Tuple[slice, slice] = np.s_[
            self.x1 + 1 : self.x2 - 1, self.y1 + 1 : self.y2 - 1
        ]
        return index

    @property
    def center(self) -> Tuple[int, int]:
        """Return the index for the rooms center coordinate."""
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2

    def intersects(self, other: Room) -> bool:
        """Return True if this room intersects with another."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )

    def distance_to(self, other: Room) -> float:
        """Return an approximate distance from this room to another."""
        x, y = self.center
        other_x, other_y = other.center
        return abs(other_x - x) + abs(other_y - y)

    def get_free_spaces(
        self, gamemap: gamemap.GameMap, number: int
    ) -> Iterator[Tuple[int, int]]:
        """Iterate over the x,y coordinates of up to `number` spaces."""
        for _ in range(number):
            x = random.randint(self.x1 + 1, self.x2 - 2)
            y = random.randint(self.y1 + 1, self.y2 - 2)
            if gamemap.is_blocked(x, y):
                continue
            yield x, y

    def place_entities(self, gamemap: gamemap.GameMap) -> None:
        """Spawn entities within this room."""
        monsters = random.randint(0, 1)
        items = random.randint(0, 2)
        for xy in self.get_free_spaces(gamemap, monsters):
            fighter.Guard.spawn(gamemap[xy])

        for xy in self.get_free_spaces(gamemap, items):
            item.Pistol().place(gamemap[xy])


def generate(width: int, height: int) -> gamemap.GameMap:
    """Return a randomly generated GameMap."""
    room_max_size = 10
    room_min_size = 6
    max_rooms = 30
    AREA_BORDER = 20

    gm = gamemap.GameMap(width, height)
    gm.tiles[...] = FLOOR
    rooms: List[Room] = []

    for i in range(max_rooms):
        # random width and height
        w = random.randint(room_min_size, room_max_size)
        h = random.randint(room_min_size, room_max_size)
        # random position without going out of the boundaries of the map
        x = random.randint(AREA_BORDER, width - AREA_BORDER - w)
        y = random.randint(AREA_BORDER, height - AREA_BORDER - h)
        new_room = Room(x, y, w, h)
        if any(new_room.intersects(other) for other in rooms):
            continue  # This room intersects with a previous room.

        # Mark room inner area as open.
        gm.tiles[new_room.outer] = WALL
        gm.tiles[new_room.inner] = FLOOR
        if rooms:
            # Open a tunnel between rooms.
            if random.randint(0, 99) < 80:
                # 80% of tunnels are to the nearest room.
                other_room = min(rooms, key=new_room.distance_to)
            else:
                # 20% of tunnels are to the previous generated room.
                other_room = rooms[-1]
            t_start = new_room.center
            t_end = other_room.center
            if random.randint(0, 1):
                t_middle = t_start[0], t_end[1]
            else:
                t_middle = t_end[0], t_start[1]
            gm.tiles[libtcodpy.line_where(*t_start, *t_middle)] = FLOOR
            gm.tiles[libtcodpy.line_where(*t_middle, *t_end)] = FLOOR
        rooms.append(new_room)

    # Add player to the first room.
    gm.player = fighter.Player.spawn(gm[5, height - 5], ai_cls=ai.PlayerControl)
    gm.actors.append(gm.player)

    for room in rooms:
        room.place_entities(gm)

    gm.update_fov()
    return gm
