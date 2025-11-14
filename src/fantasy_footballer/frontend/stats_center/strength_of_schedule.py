"""Module for the Strength of Schedule page."""

from backend.db import DbManager
from frontend.utils import (common_header, format_field_name, get_current_year,
                            get_owner_names_by_year, get_years_by_owner_id,
                            table)
from nicegui import ui


class SosDropDownSelection:
    """Class for dropdown selection for Players table."""

    DEFAULT = {
        "year": get_current_year(),
        "owner_name": "ALL",
    }

    def __init__(self):
        """Initialize DropDownSelection."""
        self.reset()

    def reset(self):
        """Reset all instance attributes to DEFAULT constant."""
        for attribute, value in SosDropDownSelection.DEFAULT.items():
            setattr(self, attribute, value)
        sos_data_table.refresh()

    def get_filter(self, field):
        """Return SQL boolean expression filtering 'field' parameter."""
        if getattr(self, field) == "ALL":
            return "1 = 1"
        return f"{field}::varchar='{getattr(self, field)}'"


def filter_dropdown_button(selection: SosDropDownSelection, field: str, field_options: list[str],
                           extra_format_funcs=None):
    """Generic dropdown button element with label above."""
    field_label = format_field_name(field, extra_format_funcs)
    with ui.column().classes("gap-1 mx-auto"):
        ui.label(field_label).classes("h-full mx-auto text-l text-weight-bold underline")
        with ui.dropdown_button(field_label, auto_close=True) as field_dropdown:
            field_dropdown.bind_text_from(selection, field)
            for field_option in ["ALL"] + field_options:
                ui.item(field_option,
                        on_click=lambda field_option=field_option: refresh_table(selection, field, field_option))


def filter_ui(selection: SosDropDownSelection):
    """UI Element containing all user input options."""
    with ui.card().classes("w-full my-auto mx-auto"):
        with ui.row().classes("w-full gap-4 my-auto mx-auto"):
            filter_dropdown_button(selection, "year", [str(year) for year in get_years_by_owner_id()])
            filter_dropdown_button(selection, "owner_name", get_owner_names_by_year())
            ui.button("Reset Filter", on_click=selection.reset)


@ui.refreshable
def sos_data_table(selection):
    """Data table displaying all sos data."""
    player_data_df = DbManager.query(f"""
        select 
            year            as Year, 
            owner_name      as "Owner Name",
            sos             as "Strength of Schedule", 
            sosr            as "Strength of Schedule Remaining", 
        from main_marts.strength_of_schedule
        where   
            {selection.get_filter('year')} and
            {selection.get_filter('owner_name')}
        order by 3 desc
    """)

    table(player_data_df,
          pagination=25,
          classes="mx-auto w-full",
          format_field_names=False,
          hidden_fields=[field for field, value in selection.__dict__.items() if value != "ALL"],
          )


def refresh_table(selection, field, value):
    """Refresh table with new year and position."""
    setattr(selection, field, value)
    sos_data_table.refresh(selection)


def sos_and_dropdowns():
    """Dropdowns and Table for Players page."""
    selection = SosDropDownSelection()
    filter_ui(selection)
    sos_data_table(selection)


@ui.page("/stats_center/strength_of_schedule")
def page():
    """Players page."""
    common_header()
    sos_and_dropdowns()
