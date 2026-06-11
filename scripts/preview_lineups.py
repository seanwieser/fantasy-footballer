"""
Throwaway visual harness for the new League-Highlights "Lineups" By-Season section.

Renders the *real* `render_season` from the league-highlights module against the already-built DuckDB
on a spare port, so the best/worst lineup-setter title cards can be screenshotted headless (see
scripts/preview_run.py) without auth or a live boot. Not part of the app.
"""
import frontend.stats_center.league_highlights as lh
from nicegui import app, ui

PORT = 8099


@ui.page("/")
def preview():
    """Render the 2024 By-Season highlight panel (which includes the Lineups section)."""
    ui.dark_mode(value=True)  # match the live app so contrast reads true
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-6xl w-full gap-2"):
            ui.label("League Highlights — 2024 By Season").classes("text-2xl font-semibold")
            lh.render_season(2024, lh._owner_info())  # pylint: disable=protected-access


@app.get("/quit")
def _quit():
    """Graceful teardown hook used by the orchestrator (no kill needed)."""
    app.shutdown()
    return "bye"


ui.run(port=PORT, show=False, reload=False)
