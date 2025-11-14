"""Module for the Postseason History page."""

from frontend.utils import common_header
from nicegui import ui


@ui.page("/stats_center/postseason_history")
async def page():
    """Postseason History page."""
    common_header()
    ui.label("Coming Soon...")
