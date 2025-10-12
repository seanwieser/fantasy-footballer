from frontend.utils import common_header
from nicegui import ui


@ui.page("/stats_center/draft_analysis")
async def page():
    """Draft Analysis page."""
    common_header()
    ui.label("Coming Soon...")
