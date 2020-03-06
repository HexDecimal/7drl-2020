from __future__ import annotations

from typing import Tuple, TYPE_CHECKING

import tcod.console

if TYPE_CHECKING:
    from tcod.console import Console
    from model import Model


UI_WIDTH = 30


def render_bar(
    console: tcod.console.Console,
    x: int,
    y: int,
    width: int,
    text: str,
    fullness: float,
    fg: Tuple[int, int, int],
    bg: Tuple[int, int, int],
) -> None:
    """Render a filled bar with centered text."""
    console.print(x, y, text.center(width)[:width], fg=(255, 255, 255))
    bar_bg = console.tiles_rgb["bg"][x : x + width, y]
    bar_bg[...] = bg
    fill_width = max(0, min(width, int(fullness * width)))
    bar_bg[:fill_width] = fg


def draw_main_view(model: Model, console: Console) -> None:
    bar_width = 20
    player = model.player
    if player.location:
        model.active_map.camera_xy = player.location.xy

    console_world = tcod.console.Console(
        console.width - UI_WIDTH, console.height, order="F"
    )
    console_ui = tcod.console.Console(UI_WIDTH, console.height, order="F")
    model.active_map.render(console_world)

    render_bar(
        console,
        1,
        console.height - 2,
        bar_width,
        f"HP: {player.fighter.hp:02}/{player.fighter.max_hp:02}",
        player.fighter.hp / player.fighter.max_hp,
        (0x40, 0x80, 0),
        (0x80, 0, 0),
    )

    x = 1
    y = console_ui.height
    log_width = console_ui.width - 1
    for text in model.log[::-1]:
        y -= tcod.console.get_height_rect(log_width, str(text))
        if y < 7:
            break
        console_ui.print_box(x, y, log_width, 0, str(text))

    console.tiles[:-UI_WIDTH, :] = console_world.tiles
    console.tiles[-UI_WIDTH:, :] = console_ui.tiles
