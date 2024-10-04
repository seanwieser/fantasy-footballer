"""Home page for the frontend."""

from backend.io_utils import MEDIA_PATH_TEMPLATE
from frontend.utils import common_header, table
from inflection import humanize, titleize
from nicegui import app, ui

CARD_INFOS = {
    "commisioner": {
        "name": "casey_magid",
        "statement": """
        Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate.
        """
    },
    "chief_enforcement_officer": {
        "name": "adam_barrett",
        "statement": """
        Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate.
        """
    },
    "current_champion": {
        "name": "aditya_sinha",
        "statement": """
        Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate.
        """
    }
}


async def owner_card(role: str):
    """Elements to highlight key owners on the splash page."""
    with ui.card().tight().classes("no-shadow border-[0px]"):
        with ui.card_section().classes("mx-auto").classes("p-0"):
            with ui.row():
                ui.label(titleize(role)).classes("text-weight-bold underline text-xl")
        image_path = MEDIA_PATH_TEMPLATE.substitute(sub_path="owners", file_name=f"{CARD_INFOS[role]['name']}.jpg")
        ui.image(image_path).props("fit=scale-down")
        with ui.card_section().classes("mx-auto p-0"):
            with ui.row().classes("place-content-center text-weight-bold underline text-base"):
                ui.link(titleize(CARD_INFOS[role]["name"]), f"/owners/{CARD_INFOS[role]['name']}")
            with ui.row().classes("text-center italic"):
                ui.label(CARD_INFOS[role]["statement"])


@ui.page("/")
async def page():
    """Home page."""
    common_header()
    with ui.grid(columns=len(CARD_INFOS)).classes("gap-1 w-2/3 fixed-bottom-left pb-3 h-fit"):
        for role in CARD_INFOS:
            await owner_card(role)
    with ui.card().classes("no-shadow border-[0px] relative-top-left"):
        with ui.card_section().classes("mx-auto").classes("p-0 pt-2"):
            ui.label("Shotgun Tracker").classes("text-weight-bold underline text-xl text-center")
        data = [
            {"owner": "casey_magid", "due": "1", "completed": "1"},
            {"owner": "adam_barrett", "due": "1", "completed": "1"},
            {"owner": "aditya_sinha", "due": "1", "completed": "1"},
            {"owner": "casey_magid", "due": "1", "completed": "1"},
            {"owner": "casey_magid", "due": "1", "completed": "1"},
            {"owner": "adam_barrett", "due": "1", "completed": "1"},
            {"owner": "aditya_sinha", "due": "1", "completed": "1"},
            {"owner": "casey_magid", "due": "1", "completed": "1"},
            {"owner": "casey_magid", "due": "1", "completed": "1"},
            {"owner": "adam_barrett", "due": "1", "completed": "1"},
            {"owner": "aditya_sinha", "due": "1", "completed": "1"},
            {"owner": "casey_magid", "due": "1", "completed": "1"},

        ]
        await table(data, classes="no-shadow border-[0px]", props="dense")

    with ui.right_drawer(fixed=True).style().props("width=500"):
        ui.label("Current Leaderboard").classes("text-weight-bold underline text-xl text-center w-full")
        data = [
            {"owner": "casey_magid", "win": "1", "loss": "1"},
            {"owner": "adam_barrett", "win": "1", "loss": "1"},
            {"owner": "aditya_sinha", "win": "1", "loss": "1"},
            {"owner": "casey_magid", "win": "1", "loss": "1"},
            {"owner": "casey_magid", "win": "1", "loss": "1"},
            {"owner": "adam_barrett", "win": "1", "loss": "1"},
            {"owner": "aditya_sinha", "win": "1", "loss": "1"},
            {"owner": "casey_magid", "win": "1", "loss": "1"},
            {"owner": "casey_magid", "win": "1", "loss": "1"},
            {"owner": "adam_barrett", "win": "1", "loss": "1"},
            {"owner": "aditya_sinha", "win": "1", "loss": "1"},
            {"owner": "casey_magid", "win": "1", "loss": "1"},
        ]
        await table(data, classes="no-shadow border-[0px] w-full")
