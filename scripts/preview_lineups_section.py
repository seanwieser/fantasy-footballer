"""
Throwaway visual harness for the League Highlights Lineups section (split titles + underutilized).

Renders the *real* all-time and by-season Lineups cards against the built DuckDB on a spare port so
the new metric cards can be screenshotted headless. Not part of the app.
"""
import backend.db as db_mod  # noqa: F401  (import side-effect: configures DbManager path)
import frontend.stats_center.league_highlights as lh
from backend.db import DbManager
from nicegui import app, ui

PORT = 8099


@ui.page("/")
def preview():
    """Render the Lineups section for both views."""
    ui.dark_mode(value=True)
    owners = lh._owner_info()  # pylint: disable=protected-access
    catalog = DbManager.query("""
        select metric_key, section, metric_label, description, empty_label
        from main_seed_data.season_highlight_metrics
        where section = 'Lineups'
        order by display_order
    """, to_dict=True)
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-7xl w-full gap-2"):
            ui.label("All-Time · Lineups").classes("text-2xl font-bold text-amber-8 mt-2")
            lh.all_time_section("Lineups", owners)
            ui.separator()
            ui.label("By Season 2024 · Lineups").classes("text-2xl font-bold text-amber-8 mt-6")
            lh.render_season_section("Lineups", catalog, 2024, owners)


@app.get("/quit")
def _quit():
    """Graceful teardown hook used by the orchestrator (no kill needed)."""
    app.shutdown()
    return "bye"


ui.run(port=PORT, show=False, reload=False)
