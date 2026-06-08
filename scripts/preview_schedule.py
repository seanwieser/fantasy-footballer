"""
Throwaway visual harness for the real owner-spotlight season-schedule table.

Monkeypatches DbManager.query to feed `season_schedule_table` a mock result frame
(Casey-2018 flag pattern, incl. a clutch + unlucky-loss overlap in Wk8 and an unplayed
week), so the dense q-table + chip slot can be screenshotted headless. Not part of the app.
"""
import asyncio

import backend.db as db_mod
import frontend.owner_history.spotlight as sp
import pandas as pd
from nicegui import app, ui

PORT = 8099


def _row(week, opp, outcome, sf, sa, flags=()):
    """Build one result-frame row matching season_schedule_table's SELECT aliases."""
    played = outcome != ""
    row = {"Week": week, "Team_Name": opp, "Owner": opp, "Outcome": outcome,
           "Points_For": f"{sf:.2f}" if played else "",
           "Points_Against": f"{sa:.2f}" if played else "", "Highlights": ""}
    row.update({flag: flag in flags for flag in sp.SCHEDULE_FLAGS})
    return row


ROWS = [
    _row(1, "Jack Hayes", "W", 187.5, 145.6),
    _row(2, "Liam Bourke", "W", 151.08, 142.2, ["is_clutch_win", "is_tightest_game"]),
    _row(3, "Sam Waterstone", "L", 88.26, 132.1, ["is_shotgun", "is_worst_week"]),
    _row(4, "Austin Warner", "L", 141.06, 150.5, ["is_unlucky_loss"]),
    _row(5, "Nick Contarino", "W", 109.42, 95.0, ["is_lucky_win"]),
    _row(8, "Adam Barrett", "L", 173.42, 178.0, ["is_clutch_loss", "is_unlucky_loss"]),
    _row(11, "Casey Magid", "W", 204.92, 120.0, ["is_best_week", "is_biggest_blowout"]),
    _row(14, "Samir Seshadri", "", 0.0, 0.0),
]

db_mod.DbManager.query = staticmethod(lambda *a, **k: pd.DataFrame(ROWS))


@ui.page("/")
def preview():
    """Render the real schedule table at the page's column width."""
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.element("div").style("width:680px"):
            sp.season_schedule_table("3", 2018)


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


ui.run(port=PORT, show=False, reload=False, title="schedule-preview")
