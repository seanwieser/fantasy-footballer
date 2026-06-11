"""
Throwaway visual harness for the owner-spotlight weekly Roster view (actual vs optimal lineup).

Renders the *real* `weekly_roster_view` against the already-built DuckDB on a spare port so the
side-by-side lineup + points-left can be screenshotted headless. Not part of the app.
"""
import backend.db as db_mod
import frontend.owner_history.spotlight as sp
from nicegui import app, ui

PORT = 8099


@ui.page("/")
def preview():
    """Render Week 1 (a week with bench mistakes) then the All ledger."""
    ui.dark_mode(value=True)  # match the live app so contrast reads true
    owner_id = db_mod.DbManager.query(
        "select owner_id from main_marts.owner_year_map where owner_name = 'Sean Wieser' limit 1",
        to_dict=True)[0]["owner_id"]
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-3xl w-full gap-4"):
            ui.label("Roster tab — Week 1 (actual vs optimal)").classes("text-2xl font-semibold")
            sp.weekly_roster_view(owner_id, 2025, 1)
            ui.separator()
            ui.label("Roster tab — Week 15 (postseason)").classes("text-2xl font-semibold")
            sp.weekly_roster_view(owner_id, 2025, 15)
            ui.separator()
            ui.label("Roster tab — All (season roster)").classes("text-2xl font-semibold")
            sp._season_roster(owner_id, 2025)  # pylint: disable=protected-access


@app.get("/quit")
def _quit():
    """Graceful teardown hook used by the orchestrator (no kill needed)."""
    app.shutdown()
    return "bye"


ui.run(port=PORT, show=False, reload=False)
