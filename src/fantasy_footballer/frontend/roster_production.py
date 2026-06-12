"""Module for the Roster Production page — what each player produced for the owner who rostered them."""

from backend.db import DbManager
from frontend.utils import (VALID_POSITIONS, common_header, format_field_name,
                            get_current_year, get_owner_names_by_year,
                            get_years_by_owner_id, table)
from nicegui import ui

# Column -> plain-English definition, surfaced in the "What do these mean?" legend so the two
# different utilization rates can't be misread.
COLUMN_GLOSSARY = [
    ("Weeks", "Regular-season weeks the owner rostered the player (bench weeks included)."),
    ("Started", "Of those weeks, how many the player was in the owner's active lineup."),
    ("Rostered Pts", "Points the player scored while on this roster — started or benched."),
    ("Started Pts", "Points the player scored in the owner's lineup — what the team actually benefited from."),
    ("Total Pts", "The player's full regular-season total across every team that rostered them."),
    ("Capture %", "Started Pts ÷ Total Pts — the share of the player's whole season this owner's lineup got. "
                  "Low when the player was only rostered part of the year (a trade/late pickup), even if "
                  "every week they were held was started."),
    ("Roster Util %", "Started Pts ÷ Rostered Pts — of the points scored while on this roster, the share the "
                      "owner actually started. Pure start/sit: ~100% means you started them whenever you had them."),
]


class DropDownSelection:
    """Class for dropdown selection for the Roster Production table."""

    @classmethod
    def defaults(cls):
        """Default selections, resolved at call time so there is no DB access at import."""
        return {
            "year": get_current_year(),
            "owner_name": "ALL",
            "position": "ALL",
        }

    def __init__(self):
        """Initialize DropDownSelection."""
        self.reset()

    def reset(self):
        """Reset all instance attributes to their defaults."""
        for attribute, value in self.defaults().items():
            setattr(self, attribute, value)
        roster_production_table.refresh()

    def get_filter(self, field):
        """Return SQL boolean expression filtering 'field' parameter."""
        if getattr(self, field) == "ALL":
            return "1 = 1"
        return f"{field}::varchar='{getattr(self, field)}'"


def filter_dropdown_button(selection: DropDownSelection, field: str, field_options: list[str]):
    """Generic dropdown button element with label above."""
    field_label = format_field_name(field)
    with ui.column().classes("gap-1 mx-auto"):
        ui.label(field_label).classes("h-full mx-auto text-l text-weight-bold underline")
        with ui.dropdown_button(field_label, auto_close=True) as field_dropdown:
            field_dropdown.bind_text_from(selection, field)
            for field_option in ["ALL"] + field_options:
                ui.item(field_option,
                        on_click=lambda field_option=field_option: refresh_table(selection, field, field_option))


def filter_ui(selection: DropDownSelection):
    """UI element containing all user input options."""
    with ui.card().classes("w-full my-auto mx-auto"):
        with ui.row().classes("w-full gap-4 my-auto mx-auto"):
            filter_dropdown_button(selection, "year", [str(year) for year in get_years_by_owner_id()])
            filter_dropdown_button(selection, "owner_name", get_owner_names_by_year())
            filter_dropdown_button(selection, "position", VALID_POSITIONS)
            ui.button("Reset Filter", on_click=selection.reset)


def legend():
    """Collapsible glossary so the capture vs. roster-utilization distinction is never ambiguous."""
    with ui.expansion("What do these columns mean?", icon="help_outline").classes("w-full"):
        with ui.column().classes("gap-1 p-2"):
            for name, definition in COLUMN_GLOSSARY:
                with ui.row().classes("gap-2 no-wrap items-baseline"):
                    ui.label(name).classes("text-weight-bold shrink-0 w-32")
                    ui.label(definition).classes("text-sm opacity-80")


@ui.refreshable
def roster_production_table(selection):
    """Data table of per-player roster production for the filtered owner-season(s)."""
    roster_df = DbManager.query(f"""
        select
            year                     as "Year",
            owner_name               as "Owner",
            owner_id                 as "Owner Id",
            player_name              as "Player",
            position                 as "Position",
            weeks_held               as "Weeks",
            weeks_started            as "Started",
            points_held              as "Rostered Pts",
            points_started           as "Started Pts",
            player_reg_season_points as "Total Pts",
            round(capture_rate * 100, 1)       as "Capture %",
            round(roster_utilization * 100, 1) as "Roster Util %"
        from main_marts.owner_roster_production
        where
            {selection.get_filter('year')} and
            {selection.get_filter('owner_name')} and
            {selection.get_filter('position')}
        order by points_started desc, points_held desc
    """)

    # Hide the active filter columns plus the cross-link id; owner_name maps to the "Owner" header.
    hidden = [field for field, value in selection.__dict__.items() if value != "ALL"]
    hidden = ["Owner" if field == "owner_name" else field for field in hidden] + ["owner_id"]
    roster_table = table(roster_df,
                         pagination=25,
                         classes="mx-auto w-full cursor-pointer",
                         format_field_names=False,
                         hidden_fields=hidden)
    roster_table.on(
        "rowClick",
        lambda event: ui.navigate.to(
            f"/owner_history/{event.args[1]['Owner Id']}/{event.args[1]['Year']}"))


def refresh_table(selection, field, value):
    """Refresh table with a new selection."""
    setattr(selection, field, value)
    roster_production_table.refresh(selection)


def roster_production_and_dropdowns():
    """Dropdowns, legend, and table for the Roster Production page."""
    selection = DropDownSelection()
    filter_ui(selection)
    legend()
    roster_production_table(selection)


@ui.page("/roster_production")
def page():
    """Roster Production page."""
    common_header()
    roster_production_and_dropdowns()
