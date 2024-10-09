"""Module for Owners page."""

import datetime

from backend.fetch import START_YEAR
from backend.io_utils import MEDIA_PATH_TEMPLATE
from backend.models import Team
from frontend.utils import common_header, image_path_to_owner_name, query_data
from inflection import titleize
from nicegui import events, ui
from sqlalchemy import func, select


def mouse_handler(event: events.MouseEventArguments):
    """Mouse event handler for Owners page images."""
    owner_full_name = image_path_to_owner_name(event.sender.source)
    if event.type == "mouseup":
        ui.navigate.to(f"/owners/{owner_full_name}")
    elif event.type == "mouseover" and owner_full_name == "jack_hayes":
        ui.notify("Dick sucks at fantasy football")


def owners_grid(img_paths):
    """Grid component for each tab."""
    with ui.grid(rows=2, columns=6).classes("h-100 gap-1"):
        for img_path in sorted(img_paths):
            label_text = titleize(image_path_to_owner_name(img_path))
            with ui.interactive_image(
                    img_path,
                    on_mouse=mouse_handler,
                    events=["mousedown", "mouseup", "mouseover"]):
                label_class = [
                    "absolute-bottom", "text-center", "text-weight-bold",
                    "bg-black", "text-white", "p-0", "m-1", "rounded-lg"
                ]
                ui.label(label_text).classes(" ".join(label_class))


async def get_img_paths_by_year():
    """Query database for owners by year and construct image paths."""
    owner_field_label = "owners"
    executable = (select(Team.year, func.array_agg(Team.owner).label(owner_field_label)).group_by(Team.year))
    rows = await query_data(executable)

    # Transform query results into dictionary of image paths by year
    img_paths = {}
    for row in rows:
        img_paths[row["year"]] = []
        for full_name in row[owner_field_label]:
            image_path = MEDIA_PATH_TEMPLATE.substitute(sub_path="owners", file_name=f"{full_name}.jpg")
            img_paths[row["year"]].append(image_path)
    return img_paths


@ui.page("/owners")
async def page():
    """Owners page with tabs for each year."""
    common_header()
    img_paths_by_year = await get_img_paths_by_year()

    current_year = datetime.datetime.now().year
    with ui.tabs().classes("w-full") as tabs:
        tab_panels = {}
        for year in range(START_YEAR, current_year + 1):
            tab_panels[year] = ui.tab(str(year))

    with ui.tab_panels(tabs, value=str(current_year)).classes("w-full"):
        for year in range(START_YEAR, current_year + 1):
            with ui.tab_panel(tab_panels[year]):
                owners_grid(img_paths_by_year[year])
