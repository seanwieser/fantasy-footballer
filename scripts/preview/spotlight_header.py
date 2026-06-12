"""
Throwaway visual harness for the owner-spotlight header (owner switcher + year switcher).

Renders the real header markup against the already-built DuckDB on a spare port so the dropdown
styling can be screenshotted headless (see scripts/preview/run.py). Not part of the app.
"""
import asyncio

from frontend.utils import (get_owners_by_year, get_years_by_owner_id,
                            owner_id_to_owner_name)
from nicegui import app, ui

PORT = 8099
OWNER, YEAR = "4", 2024


@ui.page("/")
def preview():
    """Mimic the spotlight header block."""
    ui.dark_mode(value=True)
    owner_name = owner_id_to_owner_name(OWNER)
    with ui.row().classes("w-full items-center gap-3 q-px-sm"):
        with ui.dropdown_button(owner_name).props("color=primary no-caps size=xl").classes("text-weight-bold"):
            for owner in get_owners_by_year(YEAR):
                ui.item(owner["owner_name"])
        with ui.dropdown_button(str(YEAR)).props("outline no-caps size=xl").classes("text-weight-bold"):
            for fantasy_year in get_years_by_owner_id(OWNER):
                ui.item(str(fantasy_year))


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
