"""Module for Owners page."""

import datetime
import os

from backend.db import DbManager
from frontend.utils import common_header, get_years, image_path_to_owner_id
from nicegui import events, ui


def mouse_handler(event: events.MouseEventArguments, year=int):
    """Mouse event handler for Owners page image."""
    owner_id = image_path_to_owner_id(event.sender.source)
    if event.type == "mouseup":
        ui.navigate.to(f"/owners/{owner_id}/{year}")
    elif event.type == "mouseover" and str(owner_id) == "4":
        ui.notify("Dick sucks at fantasy football")


def owners_grid(owners_info, year):
    """Grid component for each tab."""
    with ui.grid(rows=2, columns=6).classes("h-100 gap-1"):
        for owner_info in owners_info:
            with ui.interactive_image(
                    owner_info["image_path"],
                    on_mouse=lambda e, year=year: mouse_handler(e, year),
                    events=["mousedown", "mouseup", "mouseover"]):
                label_class = [
                    "absolute-bottom", "text-center", "text-weight-bold",
                    "bg-black", "text-white", "p-0", "m-1", "rounded-lg"
                ]
                ui.label(owner_info["owner_name"]).classes(" ".join(label_class))


def get_owners_info_by_year():
    """Query database for owners by year and construct image paths."""
    owners_df = DbManager.query("select * from main_marts.owners_by_year")

    # Transform query results into dictionary of owner_id, owner_name by year
    owners_info_by_year = {}
    for row in owners_df.to_dict("records"):
        owners_info = []
        for owner_info in row["owners"]:
            owner_info["image_path"] = f"resources/media/owners/{owner_info["owner_id"]}.jpg"
            owners_info.append(owner_info)
        owners_info_by_year[row["year"]] = sorted(owners_info, key=lambda d: d["owner_name"])
    return owners_info_by_year


@ui.page("/owners")
def page():
    """Owners page with tabs for each year."""
    common_header()
    owners_info_by_year = get_owners_info_by_year()

    current_year = datetime.datetime.now().year
    fantasy_years = get_years()
    with ui.tabs().classes("w-full") as tabs:
        tab_panels = {}
        for year in fantasy_years:
            tab_panels[year] = ui.tab(str(year))

    with ui.tab_panels(tabs, value=str(current_year)).classes("w-full"):
        for year in fantasy_years:
            with ui.tab_panel(tab_panels[year]):
                owners_grid(owners_info_by_year[year], year)
