"""Current-season page — live standings + shotgun counter (moved off the splash hub)."""

from backend.db import DbManager
from frontend.utils import common_header, get_current_year, table
from nicegui import ui


def _link_rows_to_spotlight(tab, year):
    """Make each table row navigate to that owner's spotlight for the current season."""
    tab.on("rowClick",
           lambda event: ui.navigate.to(f"/owner_history/{event.args[1]['Owner Id']}/{year}"))


@ui.page("/current_season")
def page():
    """Current-season standings and shotgun counter."""
    common_header()
    year = get_current_year()
    with ui.grid(columns="1fr 1fr 1fr 1fr").classes("w-full gap-0"):

        # Shotgun Counter
        with ui.card().classes("no-shadow border-[1px] relative-top-left"):
            with ui.card_section().classes("mx-auto").classes("p-0 pt-2"):
                ui.label("Shotgun Counter").classes("text-weight-bold underline text-xl text-center")
            shotgun_df = DbManager.query("select * from main_marts.current_shotgun_counter")
            shotgun_table = table(shotgun_df,
                                  classes="no-shadow w-full cursor-pointer",
                                  not_sortable="all",
                                  hidden_fields=["owner_id"])
            _link_rows_to_spotlight(shotgun_table, year)

        # Current Standings
        with ui.card().classes("no-shadow border-[1px] col-span-3"):
            ui.label("Current Standings").classes("text-weight-bold underline text-xl text-center w-full")
            standings_df = DbManager.query("select * from main_marts.current_standings")
            standings_table = table(standings_df,
                                    classes="no-shadow border-[1px] w-full cursor-pointer",
                                    not_sortable=["Name", "Owner"],
                                    hidden_fields=["owner_id"])
            _link_rows_to_spotlight(standings_table, year)
