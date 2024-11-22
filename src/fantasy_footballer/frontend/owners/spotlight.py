"""Spotlight page for each owner."""
import os

from backend.db import DbManager
from frontend.utils import (common_header, get_years, owner_id_to_owner_name,
                            table)
from nicegui import ui


def season_overview_card(title, value):
    """Season Overview card."""
    with ui.card().classes("w-full h-full"):
        ui.label(title).classes("text-weight-bold underline text-xl text-center w-full")
        with ui.row().classes(" h-full w-full items-center"):
            ui.label(value).classes("text-5xl text-center text-bold w-full")


@ui.page("/owners/{owner_id}/{year}")
def page(owner_id: str, year: int): # pylint:disable=too-many-statements
    """Owner page for each owner/year combination."""
    common_header()
    with ui.grid(columns="1fr 1fr").classes("w-full"):
        owner_name = owner_id_to_owner_name(owner_id)
        ui.label(owner_name).classes("text-weight-bold underline text-4xl w-full text-right")
        fantasy_years = get_years()
        with ui.dropdown_button(str(year)).classes("w-1/6"):
            for fantasy_year in fantasy_years:
                ui.item(fantasy_year, on_click=lambda fy=fantasy_year: ui.navigate.to(f"/owners/{owner_id}/{fy}"))

    with ui.grid(columns="1fr 1fr 2fr").classes("w-full gap-1"):
        # Owner image
        img_path = f"{os.getenv('MEDIA_DIR_PATH')}/owners/{owner_id}.jpg"
        ui.image(img_path).classes("border p-1")


        # Season Overview
        season_overview_sql = f"select * from main_marts.season_overview where owner_id={owner_id} and year={str(year)}"
        season_overview_data = DbManager.query(season_overview_sql, to_dict=True)[0]
        with ui.card().classes("no-shadow border-[0px] col-span-2"):
            with ui.card_section().classes("w-full").classes("p-0"):
                ui.label("Season Overview").classes("text-weight-bold underline text-3xl text-center")
            with ui.grid(columns="1fr 1fr 1fr 1fr 1fr 1fr").classes("w-full h-full gap-2"):

                season_overview_card("Standing", season_overview_data["standing"])
                season_overview_card("Record", season_overview_data["record"])

                # Points for
                with ui.card().classes("w-full col-span-2"):
                    ui.label("Points for").classes("text-weight-bold underline text-xl text-center w-full")
                    with ui.row().classes("w-full h-full gap-1 items-center justify-center"):
                        ui.label(season_overview_data["points_for"]).classes("text-5xl")
                        ui.label("pts").classes("text-2xl")
                    with ui.row().classes("w-full h-full gap-1 items-center justify-center"):
                        ui.label(season_overview_data["points_for_per_week"]).classes("text-5xl")
                        ui.label("pts/week").classes("text-2xl")

                # Points Against
                with ui.card().classes("w-full col-span-2"):
                    ui.label("Points against").classes("text-weight-bold underline text-xl text-center w-full")
                    with ui.row().classes("w-full h-full gap-1 items-center justify-center"):
                        ui.label(season_overview_data["points_against"]).classes("text-5xl")
                        ui.label("pts").classes("text-2xl")
                    with ui.row().classes("w-full h-full gap-1 items-center justify-center"):
                        ui.label(season_overview_data["points_against_per_week"]).classes("text-5xl")
                        ui.label("pts/week").classes("text-2xl")

                season_overview_card("Streak", season_overview_data["streak"])
                season_overview_card("Clutch Record", season_overview_data["clutch_record"])
                season_overview_card("Shotguns", season_overview_data["shotguns"])
                season_overview_card("Budget", f"${season_overview_data['budget']}")
                season_overview_card("Acquisitions", season_overview_data["acquisitions"])
                season_overview_card("Trades", season_overview_data["trades"])


        # Bio
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("Bio").classes("text-weight-bold underline text-xl text-center")

        # Shotgun Tracker
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("Shotgun Tracker").classes("text-weight-bold underline text-xl text-center")
                ui.label("Under Construction...").classes("text-weight-bold underline text-xl text-center")

        # Schedule
        schedule_sql = f"select * from main_marts.schedule where owner_id={owner_id} and year={str(year)}"
        season_data_df = DbManager.query(schedule_sql)
        season_data_df.drop(["owner_id", "year"], axis=1, inplace=True)
        table(season_data_df,
              title="Season Schedule",
              classes="no-shadow border-[0px] w-full",
              props="dense",
              not_sortable="all")
