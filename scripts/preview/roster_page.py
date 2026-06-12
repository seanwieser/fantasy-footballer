"""
Throwaway visual harness for the Roster Production page.

Renders the *real* filter UI + glossary + table from the roster-production module against the
already-built DuckDB on a spare port, so the new page can be screenshotted headless (see
scripts/preview_run.py) without auth or a live boot. Not part of the app.
"""
import frontend.roster_production as rp
from nicegui import app, ui

PORT = 8099


@ui.page("/")
def preview():
    """Render the page scoped to one owner-season, with the glossary opened to show the niceties."""
    ui.dark_mode(value=True)  # match the live app so contrast reads true
    selection = rp.DropDownSelection()
    selection.year = 2025
    selection.owner_name = "Sean Wieser"
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-6xl w-full gap-2"):
            ui.label("Roster Production — Sean Wieser, 2025").classes("text-2xl font-semibold")
            rp.filter_ui(selection)
            with ui.expansion("What do these columns mean?", icon="help_outline", value=True).classes("w-full"):
                with ui.column().classes("gap-1 p-2"):
                    for name, definition in rp.COLUMN_GLOSSARY:
                        with ui.row().classes("gap-2 no-wrap items-baseline"):
                            ui.label(name).classes("text-weight-bold shrink-0 w-32")
                            ui.label(definition).classes("text-sm opacity-80")
            rp.roster_production_table(selection)


@app.get("/quit")
def _quit():
    """Graceful teardown hook used by the orchestrator (no kill needed)."""
    app.shutdown()
    return "bye"


ui.run(port=PORT, show=False, reload=False)
