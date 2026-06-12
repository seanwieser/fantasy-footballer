"""
Throwaway visual harness for the splash tile hub.

Renders the *real* `tile_grid` from the splash module (every tile, admin level forced) on a spare
port so the dense grid layout / ordering can be screenshotted headless (see scripts/preview_run.py)
without auth or a live boot. Not part of the app.
"""
import asyncio

import frontend.splash.home as splash
from nicegui import app, ui

PORT = 8099

splash.get_access_level = lambda: 2  # force admin so every tile renders


@ui.page("/")
def preview():
    """Mimic the real splash shell: the dense hub grid on a dark background."""
    ui.dark_mode(value=True)  # match the live app so contrast reads true
    with ui.column().classes("w-full items-center px-4 py-6"):
        splash.tile_grid()


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
    asyncio.create_task(_stop())  # noqa: RUF006


ui.run(port=PORT, show=False, reload=False)
