"""Module for the League Highlights page."""

from backend.db import DbManager
from frontend.utils import common_header, get_current_year
from nicegui import ui

SECTIONS = ["Scoring", "Clutch", "Matchups", "Shotgun"]
SECTION_COLORS = {"Scoring": "blue", "Clutch": "red", "Matchups": "orange", "Shotgun": "green"}
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

# Order metric types within a category so single records lead, then totals, then counts.
TYPE_ORDER = "case metric_type when 'record' then 0 when 'total' then 1 else 2 end"


def _query(sql):
    """Run a read-only query and return a list of row dicts."""
    return DbManager.query(sql, to_dict=True)


def _runs(rows, field):
    """Group an ordered row list into consecutive runs sharing the same value of `field`."""
    runs = []
    for row in rows:
        if not runs or runs[-1][0] != row[field]:
            runs.append((row[field], []))
        runs[-1][1].append(row)
    return runs


def _medal(rank):
    """Return a medal emoji for top-3 ranks, else a numbered label."""
    return MEDALS.get(rank, f"{rank}.")


def record_card(label, rows):
    """Hero card for a single-extreme record: big value, holder(s), and season/week context."""
    with ui.card().classes("w-full h-full"):
        ui.label(label).classes("text-weight-bold underline text-base text-center w-full")
        ui.label(rows[0]["display_value"]).classes("text-4xl text-bold text-center w-full")
        for row in rows:
            context = f" · {row['season_or_week']}" if row["season_or_week"] else ""
            ui.label(f"{row['owner_name']}{context}").classes("text-sm text-center w-full opacity-80")


def leaderboard_card(label, rows):
    """Medal leaderboard card for a count/total metric (rank · owner · value)."""
    with ui.card().classes("w-full h-full"):
        ui.label(label).classes("text-weight-bold underline text-base text-center w-full")
        with ui.column().classes("w-full gap-1"):
            for row in rows:
                with ui.row().classes("w-full items-center justify-between no-wrap"):
                    ui.label(f"{_medal(row['rank'])} {row['owner_name']}").classes("text-sm")
                    ui.label(row["display_value"]).classes("text-sm text-bold")


def all_time_tab():
    """All-time view: every metric grouped by section then category into a grid of cards."""
    for section in SECTIONS:
        color = SECTION_COLORS[section]
        ui.label(section).classes(f"text-2xl text-weight-bold text-{color}-8 w-full mt-4")
        rows = _query(f"""
            select *
            from main_marts.all_time_records
            where section = '{section}'
            order by category, {TYPE_ORDER}, metric_label, rank
        """)
        for category, category_rows in _runs(rows, "category"):
            if category != section:
                ui.label(category).classes("text-base italic opacity-70 w-full mt-1")
            with ui.grid(columns=3).classes("w-full gap-4"):
                for _, metric_rows in _runs(category_rows, "metric_key"):
                    label = metric_rows[0]["metric_label"]
                    if metric_rows[0]["metric_type"] == "record":
                        record_card(label, metric_rows)
                    else:
                        leaderboard_card(label, metric_rows)


def season_title_card(label, rows):
    """Card showing a season's title holder(s) and the amount."""
    with ui.card().classes("w-full h-full"):
        ui.label(label).classes("text-weight-bold underline text-sm text-center w-full")
        ui.label(", ".join(row["owner_name"] for row in rows)).classes("text-base text-bold text-center w-full")
        ui.label(rows[0]["display_value"]).classes("text-2xl text-center w-full")


def margin_card(label, rows):
    """Card listing a season's closest/most-lopsided games with opponent and week."""
    with ui.card().classes("w-full h-full"):
        ui.label(label).classes("text-weight-bold underline text-base text-center w-full")
        for row in rows:
            ui.label(f"{_medal(row['rank'])} {row['owner_name']} def. {row['opponent_name']}").classes("text-sm w-full")
            ui.label(f"by {row['display_value']} · Wk {row['week']}").classes("text-xs opacity-70 w-full pl-5")


def render_season(year):
    """Render the title-holder cards and margin leaderboards for one season."""
    titles = _query(f"""
        select *
        from main_marts.season_highlights
        where year = {year} and metric_type = 'title'
        order by category, metric_label, rank
    """)
    ui.label("Season Titles").classes("text-2xl text-weight-bold w-full mt-2")
    with ui.grid(columns=4).classes("w-full gap-4"):
        for _, metric_rows in _runs(titles, "metric_key"):
            season_title_card(metric_rows[0]["metric_label"], metric_rows)

    boards = _query(f"""
        select *
        from main_marts.season_highlights
        where year = {year} and metric_type = 'leaderboard'
        order by metric_label, rank
    """)
    ui.label("Closest & Most Lopsided").classes("text-2xl text-weight-bold w-full mt-4")
    with ui.grid(columns=2).classes("w-full gap-4"):
        for _, metric_rows in _runs(boards, "metric_key"):
            margin_card(metric_rows[0]["metric_label"], metric_rows)


def season_tab():
    """Season view: a season picker driving a refreshable panel of that year's highlights."""
    years = [str(row["year"]) for row in
             _query("select distinct year from main_marts.season_highlights order by year desc")]
    default = str(get_current_year())
    if default not in years and years:
        default = years[0]

    season_select = ui.select(years, value=default, label="Season").classes("w-40")

    @ui.refreshable
    def panel():
        """Refreshable container for the selected season's highlights."""
        render_season(int(season_select.value))

    season_select.on_value_change(panel.refresh)
    panel()


@ui.page("/stats_center/league_highlights")
def page():
    """League Highlights page."""
    common_header()
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-7xl w-full gap-2"):
            ui.label("League Highlights").classes("text-4xl font-semibold w-full text-center")
            with ui.tabs().classes("w-full") as tabs:
                all_time = ui.tab("All-Time")
                by_season = ui.tab("By Season")
            with ui.tab_panels(tabs, value=all_time).classes("w-full"):
                with ui.tab_panel(all_time):
                    all_time_tab()
                with ui.tab_panel(by_season):
                    season_tab()
