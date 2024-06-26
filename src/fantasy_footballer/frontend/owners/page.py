"""Module for Owners page."""

import datetime

from backend.fetch import START_YEAR
from backend.io_utils import MEDIA_PATH_TEMPLATE
from backend.models import Team
from frontend.utils import (add_window_resize_event, common_header,
                            image_path_to_owner_name, query_data)
from inflection import titleize
from nicegui import events, ui
from sqlalchemy import func, select


@ui.page("/owners/{owner}")
async def owner_page(owner):
    """Owner page for each owner."""
    common_header()
    ui.label(owner)
    img_path = MEDIA_PATH_TEMPLATE.substitute(sub_path="owners",
                                              file_name=f"{owner}.jpg")
    ui.image(img_path).props('fit=scale-down')


def mouse_handler(event: events.MouseEventArguments):
    """Mouse event handler for Owners page images."""
    color = "SkyBlue" if event.type == "mousedown" else "SteelBlue"
    owner_full_name = image_path_to_owner_name(event.sender.source)
    if event.type == "mousedown":
        event.sender.props(f"opacity=0.5 background={color}")
    elif event.type == "mouseup":
        ui.navigate.to(f"/owners/{owner_full_name}")
    elif event.type == "mouseover" and owner_full_name == "jack_hayes":
        ui.notify("Dick sucks at fantasy football", duration=2)


def owners_grid(img_paths):
    """Grid component for each tab."""
    with ui.grid(columns=4).classes('h-100 gap-1'):
        for img_path in img_paths:
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
    executable = select(
        Team.year,
        func.array_agg(Team.first_name + "_" +  # pylint: disable=not-callable
                       Team.last_name)).group_by(Team.year)
    img_paths = {}
    for row in await query_data(executable):
        img_paths[row[0]] = [
            MEDIA_PATH_TEMPLATE.substitute(sub_path="owners",
                                           file_name=f"{full_name}.jpg")
            for full_name in row[1]
        ]
    return img_paths


@ui.page("/owners")
async def owners_page():
    """Owners page with tabs for each year."""
    common_header()
    img_paths_by_year = await get_img_paths_by_year()

    current_year = datetime.datetime.now().year
    with ui.tabs().classes("w-full") as tabs:
        tab_panels = {}
        for year in range(START_YEAR, current_year + 1):
            tab_panels[year] = ui.tab(str(year))

    with ui.tab_panels(tabs, value=str(current_year)).classes('w-full'):
        for year in range(START_YEAR, current_year + 1):
            with ui.tab_panel(tab_panels[year]):
                owners_grid(img_paths_by_year[year])
