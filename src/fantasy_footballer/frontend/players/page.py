"""Top-level file for the Players page."""

from frontend.players.table import players_table_and_dropdowns
from frontend.utils import common_header
from nicegui import ui


@ui.page("/players")
async def page():
    """Players page."""
    common_header()
    await players_table_and_dropdowns()
