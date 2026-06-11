"""
Throwaway visual harness for the League Highlights cards.

Renders the *real* `podium_card` / `section_header` from the page module against mock
data on a spare port, so card styling can be screenshotted headless (see
`scripts/preview_run.py`) and reviewed without auth or a live DuckDB. Not part of the app.
"""
import asyncio

import frontend.stats_center.league_highlights as lh
from nicegui import app, ui

PORT = 8099

# Mock owner context: owner_id "3" is retired; seasons-played feeds cumulative subtitles.
OWNERS = lh.OwnerInfo(retired={"3"}, seasons={"0": 7, "1": 6, "2": 5, "3": 8, "4": 4})


def _row(rank, oid, name, value, *, sw=None, detail=None, kind="context", years=None):  # pylint: disable=too-many-arguments
    """Build one mock ranked row dict matching what all_time_records yields."""
    return {"rank": rank, "owner_id": oid, "owner_name": name, "display_value": value,
            "season_or_week": sw, "detail": detail, "subtitle_kind": kind, "years_won": years}


def _group(label, desc, rows):
    """Attach the metric label + tooltip to the head row (where podium_card reads them)."""
    rows[0]["metric_label"] = label
    rows[0]["description"] = desc
    return rows


# By-Season title holders, each with a "how/when/where earned" subtitle (seed / weeks / record).
# All-Time Playoff family: Biggest snub/lucky-in (records, value = teams out/under-scored) and
# career totals (count + the years it happened).
BIGGEST_SNUB = _group("Biggest snub", "The most playoff teams a snubbed owner outscored in one season.", [
    _row(1, "2", "Casey Magid", "4", sw="2018", detail="playoff teams outscored · 2018 PF"),
    _row(2, "1", "Nick Contarino", "4", sw="2022", detail="playoff teams outscored · 1867 PF"),
    _row(3, "2", "Casey Magid", "3", sw="2024", detail="playoff teams outscored · 1921 PF"),
])
CAREER_SNUBS = _group("Most career snubs", "Every season you were snubbed (not just the years you led).", [
    _row(1, "2", "Casey Magid", "3", kind="years", years="2018, 2020, 2024"),
    _row(1, "0", "Sean Wieser", "3", kind="years", years="2019, 2021, 2023"),
    _row(3, "1", "Nick Contarino", "2", kind="years", years="2021, 2022"),
])
BIGGEST_LUCKIN = _group("Biggest lucky-in", "The most teams a lucked-in owner was outscored by.", [
    _row(1, "4", "Wynham Gweemo", "4", sw="2021", detail="higher scorers left out · 1693 PF"),
    _row(2, "3", "Jack Hayes", "2", sw="2018", detail="higher scorers left out · 1702 PF"),
    _row(3, "2", "Austin Warner", "2", sw="2022", detail="higher scorers left out · 1706 PF"),
])
CAREER_LUCKINS = _group("Most career lucky-ins", "Every season you snuck in past a higher scorer.", [
    _row(1, "4", "Wynham Gweemo", "3", kind="years", years="2021, 2023, 2024"),
    _row(2, "0", "Sean Wieser", "2", kind="years", years="2020, 2022"),
    _row(3, "3", "Liam Bourke", "2", kind="years", years="2018, 2022"),
])

LAYOUT = [
    ("Scoring", "blue", [BIGGEST_SNUB, CAREER_SNUBS, BIGGEST_LUCKIN, CAREER_LUCKINS]),
]


@ui.page("/")
def preview():
    """Mimic the real page shell so spacing/colors match production."""
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-7xl w-full gap-2"):
            for section, color, groups in LAYOUT:
                ui.label(section).classes(f"text-2xl font-bold text-{color}-8 mt-6")
                with ui.grid(columns=2).classes("w-full gap-4"):
                    for group in groups:
                        if isinstance(group, dict):  # empty-state placeholder
                            # pylint: disable=invalid-sequence-index
                            lh.empty_card(group["label"], group["description"], color, group["message"])
                        else:
                            lh.podium_card(group, color, OWNERS)


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


ui.run(port=PORT, show=False, reload=False, title="highlights-preview")
