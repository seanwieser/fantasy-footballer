"""Top-level file for the Players page."""

from frontend.players.table import players_table_and_dropdowns
from frontend.utils import add_window_resize_event, common_header
from nicegui import ui
from sqlalchemy import select


@ui.refreshable
async def right_drawer_content(window_size):
    """Content for the right drawer."""
    ui.label(str(window_size))


@ui.page("/players")
async def players_page():
    """Players page."""
    window_size = add_window_resize_event()
    ui.on(
        "resize", lambda e: right_drawer_content.refresh(
            window_size.set_size(e.args["width"], e.args["height"])))

    common_header()
    await players_table_and_dropdowns()
    with ui.right_drawer(
            fixed=False).style('background-color: #ebf1fa').props('width=500'):
        await right_drawer_content(window_size)
