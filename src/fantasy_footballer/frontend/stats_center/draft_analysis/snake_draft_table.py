"""Module for the Snake Draft Analysis table."""
from backend.db import DbManager
from frontend.utils import (VALID_POSITIONS, format_field_name,
                            get_draft_type_years, get_draftpicks_round_picks,
                            get_draftpicks_rounds, get_owner_names_by_year,
                            table)
from nicegui import ui


class SnakeDraftDropDownSelection:
    """Class for dropdown selection for Snake draft table."""

    @classmethod
    def defaults(cls):
        """Default selections, resolved at call time so there is no DB access at import."""
        return {
            "year": get_draft_type_years(is_auction=False)[-1],
            "owner": "ALL",
            "position": "ALL",
            "round": "ALL",
            "round_pick": "ALL",
        }

    def __init__(self):
        """Initialize DropDownSelection."""
        self.reset()

    def reset(self):
        """Reset all instance attributes to their defaults."""
        for attribute, value in self.defaults().items():
            setattr(self, attribute, value)
        snake_draft_data_table.refresh()

    def get_filter(self, field):
        """Return SQL boolean expression filtering 'field' parameter."""
        if getattr(self, field) == "ALL":
            return "1 = 1"
        return f"{field}::varchar='{getattr(self, field)}'"


def filter_dropdown_button(selection: SnakeDraftDropDownSelection,
                           field: str,
                           field_options: list[str],
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


def filter_ui(selection: SnakeDraftDropDownSelection):
    """UI Element containing all user input options."""
    with ui.card().classes("w-full my-auto mx-auto"):
        with ui.row().classes("w-full gap-4 my-auto mx-auto"):
            filter_dropdown_button(selection, "year", [str(year) for year in get_draft_type_years(is_auction=False)])
            filter_dropdown_button(selection, "owner", get_owner_names_by_year())
            filter_dropdown_button(selection, "position", VALID_POSITIONS)
            filter_dropdown_button(selection, "round", get_draftpicks_rounds())
            filter_dropdown_button(selection, "round_pick", get_draftpicks_round_picks())


            ui.button("Reset Filter", on_click=selection.reset)


@ui.refreshable
def snake_draft_data_table(selection):
    """Data table displaying all draft data."""
    snake_analysis_data_df = DbManager.query(f"""
        select 
            year as "Year",
            owner as "Owner",
            team as "Team",
            player as "Player",
            position as "Position",
            round as "Round",
            round_pick as "Round Pick"
        from main_marts.snake_draft_table
        where   
            {selection.get_filter('year')} and
            {selection.get_filter('owner')} and
            {selection.get_filter('position')} and
            {selection.get_filter('round')} and
            {selection.get_filter('round_pick')}
        order by year desc, round, round_pick
    """)

    table(snake_analysis_data_df,
          pagination=25,
          classes="mx-auto w-full",
          format_field_names=False,
          hidden_fields=[field for field, value in selection.__dict__.items() if value != "ALL"],
    )

def refresh_table(selection, field, value):
    """Refresh table with new selection."""
    setattr(selection, field, value)
    snake_draft_data_table.refresh(selection)


def snake_draft_table_and_dropdowns():
    """Dropdowns and Table for Players page."""
    selection = SnakeDraftDropDownSelection()
    filter_ui(selection)
    snake_draft_data_table(selection)
