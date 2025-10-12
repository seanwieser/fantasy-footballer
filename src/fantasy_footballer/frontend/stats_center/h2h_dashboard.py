"""Module for the H2H Dashboard page."""

from frontend.utils import common_header
from nicegui import ui


@ui.page("/stats_center/h2h_dashboard")
async def page():
    """H2H Dashboard page."""
    common_header()
    ui.label("Coming Soon...")
