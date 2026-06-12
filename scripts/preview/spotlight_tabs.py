"""
Throwaway visual harness for the owner-spotlight schedule/roster/postseason tabs.

Renders the *real* tab table functions from the spotlight module against the already-built DuckDB
on a spare port, so the tabbed section can be screenshotted headless (see scripts/preview_run.py)
without auth or a live boot. Not part of the app.
"""
import asyncio

import frontend.owner_history.spotlight as sp
from nicegui import app, ui

PORT = 8099
OWNER, YEAR = "4", 2024  # Jack Hayes 2024 — made the postseason, so all three tabs populate


@ui.page("/")
def preview():
    """Mimic the spotlight's tabbed section (default to Postseason to show the new tab)."""
    ui.dark_mode(value=True)  # match the live app so contrast reads true
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-4xl w-full gap-2"):
            ui.label("Owner Spotlight — schedule tabs").classes("text-2xl font-semibold")
            with ui.card().classes("no-shadow border-[0px] w-full"):
                with ui.tabs().classes("w-full") as tabs:
                    regular_tab = ui.tab("Regular Season")
                    roster_tab = ui.tab("Roster")
                    postseason_tab = ui.tab("Postseason")
                with ui.tab_panels(tabs, value=roster_tab).classes("w-full").style("min-height: 620px"):
                    with ui.tab_panel(regular_tab):
                        sp.season_schedule_table(OWNER, YEAR)
                    with ui.tab_panel(roster_tab):
                        sp.weekly_roster_view(OWNER, YEAR, "All")
                    with ui.tab_panel(postseason_tab):
                        sp.postseason_schedule_table(OWNER, YEAR)


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
