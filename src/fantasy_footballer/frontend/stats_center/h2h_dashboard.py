"""Module for the H2H Dashboard page."""

from backend.db import DbManager
from frontend.utils import SECTION_COLORS, common_header
from nicegui import ui

# Section order + icons for the comparison grid. The two pairwise rivalry sections lead (the page's
# namesake, only shown for exactly two owners), then the career metric sections in seed display_order.
# Colors come from the shared SECTION_COLORS catalog.
SECTION_ORDER = [
    "The Rivalry", "Head to Head", "Record", "Scoring", "Postseason", "Matchups", "Lineups", "Shotgun",
    "Clutch", "Transactions",
]
SECTION_ICONS = {
    "The Rivalry": "local_fire_department",
    "Head to Head": "compare_arrows",
    "Record": "leaderboard",
    "Scoring": "sports_football",
    "Postseason": "emoji_events",
    "Matchups": "sports_kabaddi",
    "Shotgun": "sports_bar",
    "Clutch": "bolt",
    "Lineups": "fact_check",
    "Transactions": "swap_horiz",
}
LABEL_COL = "minmax(150px, 1.2fr)"

# The Rivalry / Head-to-Head row catalog (labels, tooltips, order, kind) lives in the git-tracked
# `h2h_rivalry_metrics` seed — read lazily in `_rivalry_catalog()` so the page carries no row metadata.
PAIR_SECTIONS = ("The Rivalry", "Head to Head")


def _owners():
    """All owners (id -> name) plus the retired set, from the owners dimension."""
    rows = DbManager.query(
        "select owner_id, owner_name, is_active from main_marts.owners order by owner_name", to_dict=True)
    options = {row["owner_id"]: row["owner_name"] for row in rows}
    retired = {row["owner_id"] for row in rows if not row["is_active"]}
    return options, retired


def _headshot(owner_id, px=48, ring=None):
    """Circular owner headshot from local media; optional colored ring."""
    classes = "rounded-full shrink-0"
    if ring:
        classes += f" ring-2 ring-{ring}-5"
    ui.image(f"resources/media/owners/{owner_id}.jpg") \
        .classes(classes).style(f"width:{px}px;height:{px}px;object-fit:cover")


def _metric_rows(owner_ids):
    """Comparison metrics grouped by section: {section: [ {label, description, color, cells{}} ]}."""
    rows = DbManager.query(f"""
        select section, metric_key, metric_label, description, sort_sign,
               owner_id, metric_value, display_value
        from main_marts.h2h_owner_metrics
        where owner_id in ({", ".join(str(oid) for oid in owner_ids)})
        order by display_order
    """, to_dict=True)

    by_metric = {}
    for row in rows:
        metric = by_metric.setdefault(row["metric_key"], {
            "section": row["section"], "label": row["metric_label"],
            "description": row["description"], "sort_sign": row["sort_sign"], "cells": {},
        })
        metric["cells"][row["owner_id"]] = {"display": row["display_value"], "value": row["metric_value"]}

    sections = {}
    for metric in by_metric.values():
        sections.setdefault(metric["section"], []).append(metric)
    return sections


def _h2h_lookup(owner_ids):
    """{(owner_id, opponent_owner_id): record dict} for the selected owners."""
    ids = ", ".join(str(oid) for oid in owner_ids)
    rows = DbManager.query(f"""
        select *
        from main_marts.h2h_matchup_records
        where owner_id in ({ids}) and opponent_owner_id in ({ids})
    """, to_dict=True)
    return {(row["owner_id"], row["opponent_owner_id"]): row for row in rows}


def _rivalry_catalog():
    """Pairwise row catalog {section: [ {metric_key, label, description, kind} ]} from the seed."""
    rows = DbManager.query("""
        select section, metric_key, label, description, kind
        from main_seed_data.h2h_rivalry_metrics
        order by display_order
    """, to_dict=True)
    catalog = {}
    for row in rows:
        catalog.setdefault(row["section"], []).append(row)
    return catalog


def _leaders(metric, owner_ids):
    """Owner ids holding the highlighted (best, per sort_sign) value — empty when nobody stands out."""
    scored = [(oid, metric["cells"].get(oid, {}).get("value")) for oid in owner_ids]
    scored = [(oid, value) for oid, value in scored if value is not None]
    # No distinction to draw when fewer than two owners have a value or they all tie.
    if len({value for _, value in scored}) <= 1:
        return set()
    best = max(value * metric["sort_sign"] for _, value in scored)
    return {oid for oid, value in scored if value * metric["sort_sign"] == best}


def section_header_cell(section, n_cols):
    """Full-width colored section banner inside the grid."""
    color = SECTION_COLORS.get(section, "grey")
    with ui.row().classes(f"items-center gap-2 mt-4 mb-1 pb-1 border-b border-{color}-4") \
            .style(f"grid-column: 1 / span {n_cols + 1}"):
        ui.icon(SECTION_ICONS.get(section, "tag"), size="1.4rem").classes(f"text-{color}-7")
        ui.label(section).classes(f"text-lg font-bold text-{color}-8")


def metric_row(metric, owner_ids):
    """One metric: a label cell + a value cell per owner, the leader(s) highlighted."""
    color = SECTION_COLORS.get(metric["section"], "grey")
    leaders = _leaders(metric, owner_ids)
    with ui.row().classes("items-center gap-1 no-wrap py-2 min-w-0"):
        ui.label(metric["label"]).classes("text-sm font-medium opacity-80 truncate")
        ui.icon("info", size="0.9rem").classes("opacity-30 shrink-0")
        if metric["description"]:
            ui.tooltip(metric["description"]).classes("text-sm max-w-xs")
    for oid in owner_ids:
        cell = metric["cells"].get(oid, {})
        lead = oid in leaders
        with ui.row().classes("items-center justify-center gap-1 no-wrap py-2 border-l border-gray-100"):
            value_classes = f"text-base font-extrabold text-{color}-7" if lead else "text-base"
            ui.label(cell.get("display") or "—").classes(value_classes)
            if lead:
                ui.label("⭐").classes("text-sm shrink-0")


def _h2h_label(label, description):
    """Left label cell for a head-to-head row, with an info icon + tooltip like the metric rows."""
    with ui.row().classes("items-center gap-1 no-wrap py-2 min-w-0"):
        ui.label(label).classes("text-sm font-medium opacity-80 truncate")
        ui.icon("info", size="0.9rem").classes("opacity-30 shrink-0")
        ui.tooltip(description).classes("text-sm max-w-xs")


def h2h_metric_row(row, owner_ids, h2h, color):
    """A per-owner rivalry stat row: each owner's own value of `row['metric_key']` vs the other owner."""
    field = row["metric_key"]
    _h2h_label(row["label"], row["description"])
    for oid in owner_ids:
        opp = next(other for other in owner_ids if other != oid)
        record = h2h.get((oid, opp))
        value = record.get(field) if record else None
        with ui.row().classes("items-center justify-center py-2 border-l border-gray-100"):
            ui.label(str(value) if value not in (None, "") else "—").classes(
                f"text-sm font-semibold text-{color}-7")


def h2h_shared_row(row, owner_ids, h2h, color):
    """A symmetric rivalry fact centered across both columns, with an arrow toward `<field>_leader`."""
    field = row["metric_key"]
    _h2h_label(row["label"], row["description"])
    record = h2h.get((owner_ids[0], owner_ids[1]))
    value = record.get(field) if record else None
    leader = record.get(f"{field}_leader") if record else None
    with ui.element("div").classes("relative flex items-center justify-center py-2 border-l border-gray-100") \
            .style(f"grid-column: 2 / span {len(owner_ids)}"):
        if leader == owner_ids[0]:
            ui.icon("arrow_back", size="1.2rem").classes(f"absolute left-4 text-{color}-6")
        ui.label(str(value) if value not in (None, "") else "—").classes(f"text-base font-semibold text-{color}-7")
        if leader == owner_ids[1]:
            ui.icon("arrow_forward", size="1.2rem").classes(f"absolute right-4 text-{color}-6")


def pair_section(section, rows, owner_ids, h2h, n_cols):
    """Render a pairwise section (The Rivalry / Head to Head) straight from the seed catalog rows."""
    color = SECTION_COLORS.get(section, "grey")
    section_header_cell(section, n_cols)
    for row in rows:
        if row["kind"] == "symmetric":
            h2h_shared_row(row, owner_ids, h2h, color)
        else:
            h2h_metric_row(row, owner_ids, h2h, color)


def h2h_unavailable_note(n_cols):
    """Full-width hint shown when 3+ owners are selected — the rivalry view needs exactly two."""
    color = SECTION_COLORS["Head to Head"]
    with ui.row().classes("items-center gap-2 mt-4 mb-1 py-2").style(f"grid-column: 1 / span {n_cols + 1}"):
        ui.icon("compare_arrows", size="1.2rem").classes(f"text-{color}-6 opacity-60")
        ui.label("Select exactly two owners to see the head-to-head rivalry.").classes("text-sm opacity-60 italic")


def render_comparison(owner_ids, names, retired):
    """The full metric-rows x owner-columns comparison grid for the selected owners."""
    if len(owner_ids) < 2:
        ui.label("Select at least two owners to compare.").classes("text-lg opacity-60 mt-6")
        return

    n_cols = len(owner_ids)
    sections = _metric_rows(owner_ids)
    h2h = _h2h_lookup(owner_ids)
    pair_catalog = _rivalry_catalog()

    with ui.element("div").classes("w-full").style(
            f"display:grid; grid-template-columns: {LABEL_COL} repeat({n_cols}, minmax(0, 1fr)); "
            "column-gap:0.5rem; align-items:center"):
        # Header row: blank label cell + a headshot/name per owner.
        ui.element("div")
        for oid in owner_ids:
            with ui.column().classes("items-center gap-1 py-2"):
                _headshot(oid, px=56, ring="grey")
                ui.label(names[oid]).classes("text-sm font-semibold text-center truncate w-full")
                if oid in retired:
                    ui.label("(retired)").classes("text-xs opacity-50")

        for section in SECTION_ORDER:
            if section in PAIR_SECTIONS:
                if len(owner_ids) == 2:
                    pair_section(section, pair_catalog.get(section, []), owner_ids, h2h, n_cols)
                elif section == "The Rivalry":  # the note stands in for both pair sections, shown once
                    h2h_unavailable_note(n_cols)
                continue
            metrics = sections.get(section)
            if not metrics:
                continue
            section_header_cell(section, n_cols)
            for metric in metrics:
                metric_row(metric, owner_ids)


@ui.page("/stats_center/h2h_dashboard")
def page():
    """H2H Dashboard page."""
    common_header()
    options, retired = _owners()
    default = []

    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-5xl w-full gap-2"):
            ui.label("Head-to-Head Dashboard").classes("text-4xl font-semibold w-full text-center")
            ui.label("Pick two or more owners and compare them across every metric").classes(
                "text-base opacity-60 w-full text-center mb-2")

            with ui.row().classes("w-full max-w-2xl mx-auto items-center gap-2"):
                picker = ui.select(
                    options, value=default, multiple=True, label="Owners",
                ).props("outlined dense use-chips").classes("grow")
                ui.button(icon="clear", on_click=lambda: picker.set_value([])) \
                    .props("flat round").tooltip("Clear selection")

            @ui.refreshable
            def grid():
                """Refreshable container reading the picker selection."""
                render_comparison(picker.value or [], options, retired)

            picker.on_value_change(grid.refresh)
            grid()
