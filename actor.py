from __future__ import annotations

import math
import sys
import traceback
from typing import TYPE_CHECKING, Optional, Tuple, Type

import numpy as np  # type: ignore
import tcod.map
from tcod import libtcodpy

from action import NoAction

if TYPE_CHECKING:
    from ai import AI
    from fighter import Fighter
    from inventory import Inventory
    from location import Location
    from tqueue import Ticket, TurnQueue


class Actor:
    def __init__(self, location: Location, fighter: Fighter, ai_cls: Type[AI]):
        self.location = location
        self.fighter = fighter
        location.map.actors.append(self)
        self.ticket: Optional[Ticket] = location.map.scheduler.schedule(0, self.act)
        self.ai = ai_cls(self)
        self._fov: Optional[np.ndarray] = None
        self.look_dir: Tuple[int, int] = (1, 0)

    def act(self, scheduler: TurnQueue, ticket: Ticket) -> None:
        if ticket is not self.ticket:
            return scheduler.unschedule(ticket)
        try:
            action = self.ai.poll()
        except NoAction:
            print(f"Unresolved action with {self}!", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return self.ai.reschedule(100)
        assert action is action.poll(), f"{action} was not fully resolved, {self}."
        action.act()

    @property
    def inventory(self) -> Inventory:
        return self.fighter.inventory

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.location!r}, {self.fighter!r})"

    def _compute_fov(self) -> None:
        radius = 9.5
        cone_width = math.tau * 1 / 8
        cone_dir = math.atan2(*self.look_dir)
        x, y = self.location.xy
        map_ = self.location.map
        self._fov = tcod.map.compute_fov(
            transparency=map_.tiles["transparent"],
            pov=(x, y),
            radius=math.ceil(radius),
            light_walls=False,
            algorithm=libtcodpy.FOV_RESTRICTIVE,
        )
        # Get the relative coordinates for the world.
        mgrid = np.mgrid[-x : -x + map_.width, -y : -y + map_.height]

        # Cull the FOV to a vision cone.
        dir_array = (np.arctan2(*mgrid) - cone_dir) % math.tau
        cone = (dir_array <= cone_width) | (dir_array >= math.tau - cone_width)
        self._fov &= cone
        self._fov[x, y] = False

        # Clip the FOV into a sphere.
        mgrid *= mgrid
        dist_square = mgrid[0] + mgrid[1]
        self._fov[dist_square >= int(radius * radius)] &= False

    @property
    def fov(self) -> np.ndarray:
        if self._fov is None:
            self._compute_fov()
        return self._fov
