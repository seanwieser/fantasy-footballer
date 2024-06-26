"""Module for displaying a table of players."""

import datetime

from backend.fetch import START_YEAR
from backend.models import Player
from frontend.utils import common_header, query_data
from inflection import humanize
from nicegui import ui
from sqlalchemy import select


class DropDownSelection:
    """Class for dropdown selection for Players table."""

    def __init__(self, year=None, position=None):
        """Initialize DropDownSelection."""
        self.year = year
        self.position = position

    def valid(self):
        """Check if year and position are valid."""
        return all([self.year, self.position])

    def set(self, year, position):
        """Set year and position."""
        if year:
            self.year = year
        if position:
            self.position = position


@ui.refreshable
async def players_table(selection):
    """Table of players."""
    if selection.valid():
        where_clause = [
            Player.year == selection.year,
            Player.position == selection.position
        ]
        rows = await query_data(select(Player).filter(*where_clause))
        rows = [row[0].to_dict() for row in rows if row]
        columns = []
        table_fields = [
            "player_key", "name", "pos_rank", "pro_team", "total_points"
        ]
        for field in table_fields:
            if field in [col.name for col in Player.__table__.columns]:
                col_dict = {
                    "name": field,
                    "label": humanize(field),
                    "field": field,
                    "sortable": True
                }
                if field == "player_key":
                    col_dict["classes"] = "hidden"
                    col_dict["headerClasses"] = "hidden"
                columns.append(col_dict)
        rows = [{k: v
                 for k, v in row.items() if k in table_fields} for row in rows]
        rows_ordered = sorted(rows,
                              key=lambda x: x["total_points"],
                              reverse=True)

        with ui.table(columns=columns,
                      rows=rows_ordered,
                      row_key="name",
                      pagination=25).props("selection=single") as table:
            table.on("selection", lambda e: ui.notify(e.args))


def refresh_table(selection, year=None, position=None):
    """Refresh table with new year and position."""
    selection.set(year, position)
    players_table.refresh(selection)


async def players_table_and_dropdowns():
    """Dropdowns and Table for Players page."""
    positions = [
        row[0] for row in await query_data(select(Player.position).distinct())
        if row
    ]
    selection = DropDownSelection(datetime.datetime.now().year, max(positions))
    with ui.row():
        with ui.dropdown_button("Year", auto_close=True) as year_dropdown:
            year_dropdown.bind_text_from(selection, "year")
            for year in range(START_YEAR, datetime.datetime.now().year + 1):
                ui.item(str(year),
                        on_click=lambda year=year: refresh_table(selection,
                                                                 year=year))

        with ui.dropdown_button("Position",
                                auto_close=True) as position_dropdown:
            position_dropdown.bind_text_from(selection, "position")
            for position in positions:
                ui.item(position,
                        on_click=lambda position=position: refresh_table(
                            selection, position=position))

    await players_table(selection)
