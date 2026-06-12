"""
Throwaway visual harness for the Postseason History page.

Renders the *real* bracket / timeline / trophy-case sections from the page module against the
already-built DuckDB on a spare port, so styling can be screenshotted headless (see
scripts/preview_run.py) without auth or a live boot. Not part of the app.
"""
import frontend.postseason_history as ph
from nicegui import app, ui

PORT = 8099


@ui.page("/")
def preview():
    """Mimic the real page shell: a 6-team bracket (with byes), a 4-team bracket, timeline, trophies."""
    ui.dark_mode(value=True)  # match the live app so contrast reads true
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-7xl w-full gap-2"):
            ui.label("Postseason History").classes("text-4xl font-semibold w-full text-center")
            ui.label("2023 brackets (with byes)").classes("text-lg opacity-70 mt-4")
            ph._render_brackets(2023)  # pylint: disable=protected-access
            ui.label("2019 brackets (4-team era)").classes("text-lg opacity-70 mt-6")
            ph._render_brackets(2019)  # pylint: disable=protected-access
            ui.label("Timeline").classes("text-lg opacity-70 mt-6")
            ph.timeline_tab()
            ui.label("Trophy Case").classes("text-lg opacity-70 mt-6")
            ph.trophy_case_tab()


@app.get("/quit")
def _quit():
    """Graceful teardown hook used by the orchestrator (no kill needed)."""


ui.run(port=PORT, show=False, reload=False)
