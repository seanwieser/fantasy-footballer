"""Module for the Player Data page."""
from backend.db import DbManager
from frontend.utils import (VALID_POSITIONS, common_header, format_field_name,
                            get_current_year, get_nfl_teams,
                            get_years_by_owner_id, table)
from nicegui import ui


class DropDownSelection:
    """Class for dropdown selection for Players table."""

    DEFAULT = {
        "year": get_current_year(),
        "position": "ALL",
        "nfl_team": "ALL",
    }

    def __init__(self):
        """Initialize DropDownSelection."""
        self.reset()

    def reset(self):
        """Reset all instance attributes to DEFAULT constant."""
        for attribute, value in DropDownSelection.DEFAULT.items():
            setattr(self, attribute, value)
        player_data_table.refresh()

    def get_filter(self, field):
        """Return SQL boolean expression filtering 'field' parameter."""
        if getattr(self, field) == "ALL":
            return "1 = 1"
        return f"{field}::varchar='{getattr(self, field)}'"


def filter_dropdown_button(selection: DropDownSelection, field: str, field_options: list[str], extra_format_funcs=None):
    """Generic dropdown button element with label above."""
    field_label = format_field_name(field, extra_format_funcs)
    with ui.column().classes("gap-1 mx-auto"):
        ui.label(field_label).classes("h-full mx-auto text-l text-weight-bold underline")
        with ui.dropdown_button(field_label, auto_close=True) as field_dropdown:
            field_dropdown.bind_text_from(selection, field)
            for field_option in ["ALL"] + field_options:
                ui.item(field_option,
                        on_click=lambda field_option=field_option: refresh_table(selection, field, field_option))


def filter_ui(selection: DropDownSelection):
    """UI Element containing all user input options."""
    with ui.card().classes("w-full my-auto mx-auto"):
        with ui.row().classes("w-full gap-4 my-auto mx-auto"):
            filter_dropdown_button(selection,"year", [str(year) for year in get_years_by_owner_id()])
            filter_dropdown_button(selection, "position", VALID_POSITIONS)
            filter_dropdown_button(selection,
                                   "nfl_team",
                                   get_nfl_teams(),
                                   [lambda s: f"{s.split(' ')[0].upper()} {s.split(' ')[1]}"]
                                   )
            ui.button("Reset Filter", on_click=selection.reset)


@ui.refreshable
def player_data_table(selection):
    """Data table displaying all player data."""
    player_data_df = DbManager.query(f"""
        select 
            year            as Year, 
            player_name     as "Player Name",
            position        as Position, 
            position_rank   as "Position Rank", 
            nfl_team        as "NFL Team",
            total_points    as "Total Points", 
            avg_points      as "Average Points" 
        from main_marts.player_data_table
        where   
            {selection.get_filter('year')} and
            {selection.get_filter('position')} and
            {selection.get_filter('nfl_team')}
    """)

    table(player_data_df,
          pagination=25,
          classes="mx-auto w-full",
          format_field_names=False,
          hidden_fields = [field for field, value in selection.__dict__.items() if value != "ALL"],
          slots=[{
              "name": "body-cell-Team Name",
              "template": r"""
                  <q-td 
                      :props="props"
                      :class="
                          props.value.includes('Available') ? 'bg-light-green-7' : 
                          'primary'      
                      ">
                      {{ props.value }}
                  </q-td>"""}
          ]
    )

def refresh_table(selection, field, value):
    """Refresh table with new year and position."""
    setattr(selection, field, value)
    player_data_table.refresh(selection)


def players_table_and_dropdowns():
    """Dropdowns and Table for Players page."""
    selection = DropDownSelection()
    filter_ui(selection)
    player_data_table(selection)

@ui.page("/stats_center/player_data")
def page():
    """Players page."""
    common_header()
    players_table_and_dropdowns()
