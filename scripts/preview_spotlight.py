"""
Throwaway visual harness for the owner-spotlight Highlights card.

Monkeypatches DbManager.query to feed the *real* `highlights_card` mock
`season_highlights` rows, so the card can be screenshotted headless (see
`scripts/preview_run.py`) without auth or a live DuckDB. Not part of the app.
"""
import asyncio

import backend.db as db_mod
import frontend.owner_history.spotlight as sp
from nicegui import app, ui

PORT = 8099

# Mock season_highlights rows (matches what the mart yields): titles are gold-only; margin
# leaderboards carry silver/bronze and a fully-composed `detail` subtitle.
HIGHLIGHTS = [
    {"section": "Scoring", "metric_label": "Scoring title", "display_value": "2052.84",
     "detail": "1st seed", "rank": 1},
    {"section": "Scoring", "metric_label": "Best-week title", "display_value": "200.5",
     "detail": "Wk 4", "rank": 1},
    {"section": "Shotgun", "metric_label": "Sober season", "display_value": "0",
     "detail": None, "rank": 1},
    {"section": "Matchups", "metric_label": "Tightest game", "display_value": "1.0",
     "detail": "def. Austin Warner · 158.36-157.36 · Wk 12", "rank": 1},
    {"section": "Matchups", "metric_label": "Biggest blowout", "display_value": "107.22",
     "detail": "def. Samir Seshadri · 200.5-93.28 · Wk 4", "rank": 2},
]

db_mod.DbManager.query = staticmethod(lambda *a, **k: list(HIGHLIGHTS))


@ui.page("/")
def preview():
    """Render the highlights card inside the narrow column it occupies on the real page."""
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.element("div").style("width:340px"):
            sp.highlights_card("10", 2023)


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


ui.run(port=PORT, show=False, reload=False, title="spotlight-preview")
