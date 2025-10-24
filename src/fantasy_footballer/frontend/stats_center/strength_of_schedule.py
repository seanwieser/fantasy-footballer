"""Module for the Strength of Schedule page."""

from frontend.utils import common_header
from nicegui import ui


@ui.page("/stats_center/strength_of_schedule")
async def page():
    """Strength of Schedule page."""
    common_header()
    ui.label("Coming Soon...")
