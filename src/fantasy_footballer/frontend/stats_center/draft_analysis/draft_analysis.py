"""Module for the Draft Analysis page."""

from frontend.stats_center.draft_analysis.auction_draft_table import \
    auction_draft_table_and_dropdowns
from frontend.stats_center.draft_analysis.snake_draft_table import \
    snake_draft_table_and_dropdowns
from frontend.utils import common_header
from nicegui import ui


@ui.page("/stats_center/draft_analysis")
def page():
    """Players page."""
    common_header()

    draft_tables = {
        "Snake": snake_draft_table_and_dropdowns,
        "Auction": auction_draft_table_and_dropdowns
    }
    with ui.tabs().classes("w-full") as tabs:
        tab_panels = {}
        for draft_type in draft_tables:
            tab_panels[draft_type] = ui.tab(draft_type)

    with ui.tab_panels(tabs, value="Auction").classes("w-full"):
        for draft_type, page_contents in draft_tables.items():
            with ui.tab_panel(tab_panels[draft_type]):
                page_contents()
