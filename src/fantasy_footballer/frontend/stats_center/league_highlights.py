from frontend.utils import common_header
from nicegui import ui


@ui.page("/stats_center/league_highlights")
async def page():
    """Highlights page."""
    common_header()
    ui.label("Coming Soon...")
