"""Module for Leaderboard page."""

from frontend.utils import common_header
from nicegui import ui


@ui.page('/leaderboard')
def leaderboard_page():
    """Leaderboard page."""
    common_header()
    ui.label("Leaderboard")
