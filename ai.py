from __future__ import annotations

import random
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod.path

from action import NoAction, Action
import actions
import states

if TYPE_CHECKING:
    from actor import Actor


class Pathfinder(Action):
    def __init__(self, actor: Actor, dest_xy: Tuple[int, int]) -> None:
        super().__init__(actor)

        map_ = self.actor.location.map
        walkable = np.copy(map_.tiles["move_cost"])
        blocker_pos = [e.location.xy for e in map_.actors]
        blocker_index = tuple(np.transpose(blocker_pos))
        walkable[blocker_index] = False
        walkable[dest_xy] = True
        self.path: List[Tuple[int, int]] = tcod.path.AStar(walkable).get_path(
            *self.actor.location.xy, *dest_xy
        )

    def poll(self) -> Action:
        if not self.path:
            raise NoAction("End of path reached.")
        return actions.MoveTo(self.actor, self.path.pop(0)).poll()


class AI(Action):
    def get_path(
        self, owner: Actor, target_xy: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        map_ = owner.location.map
        walkable = np.copy(map_.tiles["move_cost"])
        blocker_pos = [e.location.xy for e in map_.actors]
        blocker_index = tuple(np.transpose(blocker_pos))
        walkable[blocker_index] = False
        walkable[target_xy] = True
        return tcod.path.AStar(walkable).get_path(*owner.location.xy, *target_xy)


class BasicMonster(AI):
    def __init__(self, actor: Actor) -> None:
        super().__init__(actor)
        self.path: List[Tuple[int, int]] = []

    def poll(self) -> Action:
        owner = self.actor
        map_ = owner.location.map
        if map_.visible[owner.location.xy]:
            self.path = self.get_path(owner, map_.player.location.xy)
            if len(self.path) >= 25:
                self.path = []
                try:
                    return actions.MoveTowards(owner, map_.player.location.xy).poll()
                except NoAction:
                    pass
        if not self.path:
            return actions.Move(owner, (0, 0)).poll()
        if owner.location.distance_to(*map_.player.location.xy) <= 1:
            return actions.AttackPlayer(owner).poll()
        return actions.MoveTo(owner, self.path.pop(0)).poll()


class TurnRandomly(Action):
    DIRS = (
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
        (1, 0),
        (1, -1),
        (0, -1),
    )

    def act(self) -> None:
        my_dir = self.DIRS.index(self.actor.look_dir)
        my_dir += 1 if random.random() < 0.5 else -1
        my_dir %= len(self.DIRS)
        self.actor.look_dir = self.DIRS[my_dir]
        self.actor._fov = None
        self.reschedule(100)


class Wander(Action):
    def poll(self) -> Action:
        try:
            if random.random() > 0.25:
                return actions.Move(self.actor, self.actor.look_dir).poll()
        except NoAction:
            pass
        return TurnRandomly(self.actor).poll()


class RandomPatrol(Action):
    def __init__(self, actor: Actor) -> None:
        super().__init__(actor)
        self.subaction: Optional[Pathfinder] = None

    def poll(self) -> Action:
        if self.subaction:
            try:
                return self.subaction.poll()
            except NoAction:
                pass
        while True:
            dest_xy = (
                random.randint(0, self.actor.location.map.width - 1),
                random.randint(0, self.actor.location.map.height - 1),
            )
            self.subaction = Pathfinder(self.actor, dest_xy)
            try:
                return self.subaction.poll()
            except NoAction:
                pass


class GuardAI(AI):
    def __init__(self, actor: Actor) -> None:
        super().__init__(actor)
        self.pathfinder: Optional[Action] = None
        self.random_patrol = RandomPatrol(self.actor)

    def poll(self) -> Action:
        player = self.actor.location.map.player
        if self.actor.fov[player.location.xy]:
            self.pathfinder = Pathfinder(self.actor, player.location.xy)
        if self.pathfinder:
            try:
                return self.pathfinder.poll()
            except NoAction:
                self.pathfinder = None
        return self.random_patrol.poll()


class PlayerControl(AI):
    def act(self) -> None:
        ticket = self.actor.ticket
        while ticket is self.actor.ticket:
            try:
                states.PlayerReady(self.actor.location.map.model).loop()
            except NoAction as exc:
                self.report(exc.args[0])
