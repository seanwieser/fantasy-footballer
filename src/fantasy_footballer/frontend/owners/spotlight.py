"""Spotlight page for each owner."""
from backend.io_utils import MEDIA_PATH_TEMPLATE
from frontend.utils import (add_window_resize_event, common_header,
                            image_path_to_owner_name, query_data, table)
from inflection import titleize
from nicegui import ui


@ui.page("/owners/{owner}")
async def page(owner):
    """Owner page for each owner."""
    common_header()
    ui.label(titleize(owner)).classes("text-weight-bold underline text-4xl w-full text-center")
    img_path = MEDIA_PATH_TEMPLATE.substitute(sub_path="owners",
                                                  file_name=f"{owner}.jpg")
    with ui.grid(columns="1fr 2fr").classes("w-full gap-0"):
        # Top left
        ui.image(img_path).classes('border p-1')

        # Top right
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("Shotgun Tracker").classes("text-weight-bold underline text-xl text-center")
            data = [
                {"week": "casey_magid", "reason": "1", "link": "1"},
                {"week": "adam_barrett", "reason": "1", "link": "1"},
            ]
            with ui.scroll_area().classes("w-full"):
                await table(data, classes="no-shadow border-[0px] w-full virtual-scroll")

        # Bottom left
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("Bio").classes("text-weight-bold underline text-xl text-center")


        # Bottom right
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("History").classes("text-weight-bold underline text-xl text-center")
            data = [
                {"year": "casey_magid", "result": "1", "shotguns": "1"},
                {"year": "adam_barrett", "result": "1", "shotguns": "1"},
                {"year": "aditya_sinha", "result": "1", "shotguns": "1"},
                {"year": "casey_magid", "result": "1", "shotguns": "1"},
                {"year": "casey_magid", "result": "1", "shotguns": "1"},
                {"year": "adam_barrett", "result": "1", "shotguns": "1"},
                {"year": "aditya_sinha", "result": "1", "shotguns": "1"},
                {"year": "casey_magid", "result": "1", "shotguns": "1"},

            ]
            await table(data, classes="no-shadow border-[0px] w-full row-span-2")

    with ui.right_drawer(fixed=True).style().props('width=500'):
        ui.label("Schedule").classes("text-weight-bold underline text-xl text-center w-full")
        data = [
            {"week": "casey_magid", "opponent": "1", "result": "1"},
            {"week": "adam_barrett", "opponent": "1", "result": "1"},
            {"week": "aditya_sinha", "opponent": "1", "result": "1"},
            {"week": "casey_magid", "opponent": "1", "result": "1"},
            {"week": "casey_magid", "opponent": "1", "result": "1"},
            {"week": "adam_barrett", "opponent": "1", "result": "1"},
            {"week": "aditya_sinha", "opponent": "1", "result": "1"},
            {"week": "casey_magid", "opponent": "1", "result": "1"},
            {"week": "casey_magid", "opponent": "1", "result": "1"},
            {"week": "adam_barrett", "opponent": "1", "result": "1"},
            {"week": "aditya_sinha", "opponent": "1", "result": "1"},
            {"week": "casey_magid", "opponent": "1", "result": "1"},
            {"week": "adam_barrett", "opponent": "1", "result": "1"},
            {"week": "aditya_sinha", "opponent": "1", "result": "1"},
            {"week": "casey_magid", "opponent": "1", "result": "1"},
        ]
        await table(data, classes="no-shadow border-[0px] w-full virtual-scroll")
