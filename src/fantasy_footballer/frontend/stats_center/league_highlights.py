"""Module for the League Highlights page."""

from collections import namedtuple
from contextlib import contextmanager

from backend.db import DbManager
from frontend.utils import (SECTION_COLORS, common_header, get_current_year,
                            medal)
from nicegui import ui

SECTIONS = ["Scoring", "Postseason", "Matchups", "Shotgun", "Clutch", "Transactions"]
SECTION_ICONS = {"Scoring": "sports_football", "Clutch": "bolt", "Matchups": "sports_kabaddi", "Shotgun": "sports_bar",
                 "Transactions": "swap_horiz", "Postseason": "emoji_events"}

# Within a section, cards cluster by `category` for scannability (order comes from the seed's
# display_order); these are the friendly sub-cluster headers.
CATEGORY_LABELS = {"Season": "Full Season", "Matchup": "Single Week", "Playoff": "Playoff Races",
                   "Results": "Titles & Finishes"}

# Owner-level context shared across cards: retired flag (set of owner_ids) + seasons-played (dict).
OwnerInfo = namedtuple("OwnerInfo", ["retired", "seasons"])


def _runs(rows, field):
    """Group an ordered row list into consecutive runs sharing the same value of `field`."""
    runs = []
    for row in rows:
        if not runs or runs[-1][0] != row[field]:
            runs.append((row[field], []))
        runs[-1][1].append(row)
    return [rows for _, rows in runs]


def _balanced_cols(n, max_cols=3):
    """
    Pick a column count (<= max_cols) leaving the fewest empty cells in the last row.

    Keeps each card grid symmetric regardless of how many cards a section holds
    (4 -> 2x2, 6 -> 2x3, 2 -> 1x2), preferring wider grids when gaps tie.
    """
    if n <= max_cols:
        return max(n, 1)
    best, fewest_gaps = max_cols, max_cols
    for cols in range(max_cols, 1, -1):
        gaps = (cols - n % cols) % cols
        if gaps < fewest_gaps:
            best, fewest_gaps = cols, gaps
    return best


def _owner_info():
    """Retired flag + tenure (seasons played) per owner, from the owners dimension."""
    rows = DbManager.query("select owner_id, seasons_played, is_active from main_marts.owners", to_dict=True)
    retired = {row["owner_id"] for row in rows if not row["is_active"]}
    seasons = {row["owner_id"]: row["seasons_played"] for row in rows}
    return OwnerInfo(retired, seasons)


def _subtitle(row):
    """Secondary context line for a row: the `detail` string and/or season/week, joined."""
    parts = [row.get(field) for field in ("detail", "season_or_week")]
    return " · ".join(part for part in parts if part) or None


def _row_subtitle(row, owners):
    """Per-row subtitle by `subtitle_kind`: years won, tenure (seasons played), or context line."""
    kind = row.get("subtitle_kind")
    if kind == "years":
        return row.get("years_won")
    if kind == "tenure":
        return f"{owners.seasons.get(row['owner_id'], '–')} seasons"
    return _subtitle(row)


@contextmanager
def metric_card(description):
    """Styled card shell with a hover tooltip carrying the metric's explanation."""
    with ui.card().classes(
        "w-full h-full gap-2 p-4 rounded-xl shadow-sm hover:shadow-md transition-shadow"
    ) as card:
        if description:
            ui.tooltip(description).classes("text-sm max-w-xs")
        yield card


def _headshot(owner_id, px=52, ring=None):
    """Circular owner headshot from local media; optional colored ring to mark the leader."""
    classes = "rounded-full shrink-0"
    if ring:
        classes += f" ring-2 ring-offset-2 ring-{ring}-5"
    ui.image(f"resources/media/owners/{owner_id}.jpg") \
        .classes(classes).style(f"width:{px}px;height:{px}px;object-fit:cover")


def _name(row, owners, classes):
    """Owner name, bold per `classes`, with a muted (retired) tag for inactive owners."""
    with ui.row().classes("items-baseline gap-1 no-wrap min-w-0"):
        ui.label(row["owner_name"]).classes(f"{classes} truncate")
        if row["owner_id"] in owners.retired:
            ui.label("(retired)").classes("text-xs opacity-50 shrink-0")


def _card_header(label, color):
    """Card eyebrow: uppercase metric label + an info (tooltip) hint."""
    with ui.row().classes("w-full items-center justify-between no-wrap gap-2"):
        ui.label(label).classes(f"text-xs font-semibold uppercase tracking-wide text-{color}-7 truncate")
        ui.icon("info", size="1rem").classes("opacity-30 shrink-0")


def podium_card(rows, color, owners):
    """
    Unified ranked tile used for every metric (records, titles, leaderboards).

    Rank 1 is the headline — a ring-bordered headshot with a larger, bold name + value — so the
    leader pops; a thin divider separates it from ranks 2-3, which sit below compact and
    left-aligned to the same column. Values share the right edge across rows. Context sits under
    each name.
    """
    head = rows[0]
    with metric_card(head["description"]):
        _card_header(head["metric_label"], color)
        with ui.column().classes("w-full gap-2"):
            divided = False
            for row in rows:
                lead = row["rank"] == 1
                # Thin rule once, separating the headline leader(s) from the chasers.
                if not lead and not divided:
                    ui.separator().classes("opacity-30")
                    divided = True
                with ui.row().classes("w-full items-center gap-3 no-wrap"):
                    ui.label(medal(row["rank"])).classes("text-base w-7 text-center shrink-0")
                    if lead:
                        _headshot(row["owner_id"], px=44, ring=color)
                    else:
                        ui.element("div").classes("shrink-0").style("width:44px;height:1px")
                    with ui.column().classes("gap-0 min-w-0 grow"):
                        _name(row, owners, "text-base font-bold" if lead else "text-sm font-medium")
                        subtitle = _row_subtitle(row, owners)
                        if subtitle:
                            ui.label(subtitle).classes("text-xs opacity-60 truncate")
                    value_size = "text-xl font-extrabold" if lead else "text-base font-semibold"
                    ui.label(row["display_value"]).classes(f"{value_size} text-{color}-7 ml-auto shrink-0")


def _subsection(title, groups, color, owners, render):
    """A cluster of metric cards in a symmetric grid; optional header, renders nothing when empty."""
    if not groups:
        return
    if title:
        ui.label(title).classes(
            f"text-sm font-semibold uppercase tracking-wide text-{color}-6 w-full mt-3 opacity-80")
    with ui.grid(columns=_balanced_cols(len(groups))).classes("w-full gap-4"):
        for group in groups:
            render(group, color, owners)


def all_time_tab(owners):
    """All-time view: each section's cards grouped by category into scannable clusters."""
    for section in SECTIONS:
        color = SECTION_COLORS[section]
        section_header(section)
        rows = DbManager.query(f"""
            select *
            from main_marts.all_time_records
            where section = '{section}'
            order by display_order, rank
        """, to_dict=True)
        by_category = {}
        for group in _runs(rows, "metric_key"):
            by_category.setdefault(group[0]["category"], []).append(group)
        # by_category preserves seed display_order (rows are ordered by it). Only label
        # sub-clusters when a section spans multiple categories — Clutch/Shotgun are
        # single-category, so a header would just echo the section title.
        labeled = len(by_category) > 1
        for category, cat_groups in by_category.items():
            title = CATEGORY_LABELS.get(category, category) if labeled else None
            _subsection(title, cat_groups, color, owners, podium_card)


def section_header(section):
    """Section banner: color icon + title with a thin colored rule beneath it."""
    color = SECTION_COLORS[section]
    with ui.row().classes("w-full items-center gap-2 mt-8 mb-1"):
        ui.icon(SECTION_ICONS[section], size="1.9rem").classes(f"text-{color}-7")
        ui.label(section).classes(f"text-2xl font-bold text-{color}-8")
    ui.separator().classes(f"bg-{color}-4")


def empty_card(label, description, color, message):
    """Placeholder for a title nobody earned this season — keeps each section's grid consistent."""
    with metric_card(description):
        _card_header(label, color)
        with ui.column().classes("w-full grow items-center justify-center py-2"):
            ui.label(message or "Not awarded this season").classes("text-sm opacity-50 italic text-center")


def render_season(year, owners):
    """Render every season-title card (held or empty) grouped by section."""
    # Catalog drives the grid so a title with no holder this year still shows a placeholder card.
    catalog = DbManager.query("""
        select metric_key, section, metric_label, description, empty_label
        from main_seed_data.season_highlight_metrics
        order by display_order
    """, to_dict=True)
    holders = DbManager.query(f"""
        select *
        from main_marts.season_highlights
        where year = {year}
        order by display_order, rank
    """, to_dict=True)
    held = {group[0]["metric_key"]: group for group in _runs(holders, "metric_key")}

    by_section = {}
    for meta in catalog:
        by_section.setdefault(meta["section"], []).append(meta)
    for section in SECTIONS:
        metrics = by_section.get(section)
        if not metrics:
            continue
        section_header(section)
        color = SECTION_COLORS[section]
        with ui.grid(columns=_balanced_cols(len(metrics))).classes("w-full gap-4"):
            for meta in metrics:
                group = held.get(meta["metric_key"])
                if group:
                    podium_card(group, color, owners)
                else:
                    empty_card(meta["metric_label"], meta["description"], color, meta["empty_label"])


def season_tab(owners):
    """Season view: a season picker driving a refreshable panel of that year's highlights."""
    years = [str(row["year"]) for row in DbManager.query(
        "select distinct year from main_marts.season_highlights order by year desc", to_dict=True)]
    default = str(get_current_year())
    if default not in years and years:
        default = years[0]

    season_select = ui.select(years, value=default, label="Season").props("outlined dense").classes("w-40")

    @ui.refreshable
    def panel():
        """Refreshable container for the selected season's highlights."""
        render_season(int(season_select.value), owners)

    season_select.on_value_change(panel.refresh)
    panel()


@ui.page("/stats_center/league_highlights")
def page():
    """League Highlights page."""
    common_header()
    owners = _owner_info()
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-7xl w-full gap-2"):
            ui.label("League Highlights").classes("text-4xl font-semibold w-full text-center")
            ui.label("Records, titles, and bragging rights across every season").classes(
                "text-base opacity-60 w-full text-center mb-2")
            with ui.tabs().classes("w-full") as tabs:
                all_time = ui.tab("All-Time", icon="emoji_events")
                by_season = ui.tab("By Season", icon="calendar_month")
            with ui.tab_panels(tabs, value=all_time).classes("w-full"):
                with ui.tab_panel(all_time):
                    all_time_tab(owners)
                with ui.tab_panel(by_season):
                    season_tab(owners)
