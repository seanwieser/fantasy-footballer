"""
Throwaway visual harness for the H2H Dashboard comparison grid.

Renders the *real* `comparison_grid` from the page module against the already-built DuckDB on a
spare port, so the grid styling / leader highlight / H2H row can be screenshotted headless (see
scripts/preview_run.py) without auth or a live boot. Not part of the app.
"""
import asyncio

import frontend.stats_center.h2h_dashboard as h2h
from nicegui import app, ui

PORT = 8099


@ui.page("/")
def preview():
    """Mimic the real page shell and compare the first three owners."""
    ui.dark_mode(value=True)  # match the live app so contrast reads true
    options, retired = h2h._owners()  # pylint: disable=protected-access
    owner_ids = list(options.keys())[:2]
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-5xl w-full gap-2"):
            ui.label("Head-to-Head Dashboard").classes("text-4xl font-semibold w-full text-center")
            h2h.render_comparison(owner_ids, options, retired)


@app.get("/quit")
def _quit():
    """Graceful teardown hook used by the orchestrator (no kill needed)."""
    app.shutdown()
    return "bye"


@app.on_startup
async def _watchdog():
    """Safety: self-shutdown after 90s so a stray preview never lingers."""
    async def _stop():
        await asyncio.sleep(90)
        app.shutdown()
    asyncio.create_task(_stop())


ui.run(port=PORT, show=False, reload=False, title="h2h-preview")
