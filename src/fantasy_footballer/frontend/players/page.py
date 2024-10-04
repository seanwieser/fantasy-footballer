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
async def page():
    """Players page."""
    common_header()
    await players_table_and_dropdowns()
