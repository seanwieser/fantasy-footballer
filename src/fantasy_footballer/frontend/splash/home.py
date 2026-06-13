"""Splash page — the site's section-tile hub (front door to every destination)."""

from frontend.utils import common_header, get_access_level, section_tile
from nicegui import ui

# (label, material icon, Quasar color, route, min access level). The single source of the hub grid;
# tiles above the user's access level are hidden. Ordered live -> people -> marquee stats ->
# granular data -> extras. Every destination is a top-level route (no stats_center grouping).
SECTION_TILES = [
    ("Current Season", "leaderboard", "teal", "/current_season", 0),
    ("Owner History", "groups", "purple", "/owner_history", 0),
    ("League Highlights", "sym_s_star", "orange", "/league_highlights", 0),
    ("H2H Dashboard", "sym_s_swords", "red", "/h2h_dashboard", 0),
    ("Postseason History", "history", "yellow", "/postseason_history", 0),
    ("Player Data", "sym_s_data_loss_prevention", "blue", "/player_data", 0),
    ("Draft Analysis", "price_check", "green", "/draft_analysis", 0),
    ("Strength of Schedule", "sym_s_calendar_month", "grey", "/strength_of_schedule", 0),
    ("Roster Production", "inventory_2", "cyan", "/roster_production", 0),
    ("Glossary", "menu_book", "blue-grey", "/glossary", 0),
    ("Gallery", "photo_library", "pink", "/gallery", 1),
    ("Admin", "settings", "blue-grey", "/admin", 2),
]


def tile_grid():
    """The dense 4-column hub grid, gated to the current user's access level."""
    access_level = get_access_level()
    with ui.grid(columns=4).classes("max-w-5xl w-full gap-4"):
        for label, icon, color, route, level in SECTION_TILES:
            if level <= access_level:
                section_tile(label=label, icon=icon, icon_color=color, route=route)


@ui.page("/")
def page():
    """Home page: the tile hub."""
    common_header()
    with ui.column().classes("w-full items-center px-4 py-6 no-shadow"):
        tile_grid()
