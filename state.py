from __future__ import annotations

import tcod.console
import tcod.event
from tcod import libtcodpy
from tcod.event import KeySym

CONSOLE_MIN_SIZE = (60, 16)  # The smallest acceptable main console size.
g_console: tcod.console.Console  # Global console object.


class State(tcod.event.EventDispatch):
    MOVE_KEYS = {
        KeySym.LEFT: (-1, 0),
        KeySym.RIGHT: (1, 0),
        KeySym.UP: (0, -1),
        KeySym.DOWN: (0, 1),
        KeySym.HOME: (-1, -1),
        KeySym.END: (-1, 1),
        KeySym.PAGEUP: (1, -1),
        KeySym.PAGEDOWN: (1, 1),
        KeySym.KP_1: (-1, 1),
        KeySym.KP_2: (0, 1),
        KeySym.KP_3: (1, 1),
        KeySym.KP_4: (-1, 0),
        KeySym.KP_5: (0, 0),
        KeySym.KP_6: (1, 0),
        KeySym.KP_7: (-1, -1),
        KeySym.KP_8: (0, -1),
        KeySym.KP_9: (1, -1),
        KeySym.H: (-1, 0),
        KeySym.J: (0, 1),
        KeySym.K: (0, -1),
        KeySym.L: (1, 0),
        KeySym.Y: (-1, -1),
        KeySym.U: (1, -1),
        KeySym.B: (-1, 1),
        KeySym.N: (1, 1),
        KeySym.PERIOD: (0, 0),
        KeySym.CLEAR: (0, 0),
    }

    COMMAND_KEYS = {
        KeySym.D: "drop",
        KeySym.I: "inventory",
        KeySym.G: "pickup",
        KeySym.ESCAPE: "quit",
    }

    def __init__(self) -> None:
        self.running = False

    def loop(self) -> None:
        """Run a state based game loop."""
        global g_console
        self.running = True
        while self.running:
            self.on_draw(g_console)
            libtcodpy.console_flush(g_console)
            for event in tcod.event.wait():
                if event.type == "WINDOWRESIZED":
                    g_console = configure_console()
                self.dispatch(event)
                if not self.running:
                    break  # Events may set self.running to False.

    def on_draw(self, console: tcod.console.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.cmd_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym in self.COMMAND_KEYS:
            getattr(self, f"cmd_{self.COMMAND_KEYS[event.sym]}")()
        elif event.sym in self.MOVE_KEYS:
            self.cmd_move(*self.MOVE_KEYS[event.sym])

    def cmd_quit(self) -> None:
        """Save and quit."""
        raise SystemExit()

    def cmd_move(self, x: int, y: int) -> None:
        pass

    def cmd_pickup(self) -> None:
        pass

    def cmd_inventory(self) -> None:
        pass

    def cmd_drop(self) -> None:
        pass


def configure_console() -> tcod.console.Console:
    """Return a new main console with an automatically determined size."""
    width, height = tcod.console.recommended_size()
    width = max(width, CONSOLE_MIN_SIZE[0])
    height = max(height, CONSOLE_MIN_SIZE[1])
    return tcod.console.Console(width, height, order="F")
