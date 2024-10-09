"""Home page for the frontend."""

from datetime import datetime

from backend.io_utils import MEDIA_PATH_TEMPLATE
from backend.models import Team
from frontend.utils import common_header, query_data, table
from inflection import titleize
from nicegui import ui
from sqlalchemy import String, cast, func, select, text

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
    },
    "current_loser": {
        "name": "samir_seshadri",
        "statement": """
    Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate.
    """
    }
}


async def owner_card(role: str):
    """Elements to highlight key owners on the splash page."""
    with ui.card().tight().classes("no-shadow border-[1px]"):
        with ui.card_section().classes("mx-auto").classes("p-0"):
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
    with ui.grid(columns="1fr 1fr 1fr 1fr").classes("w-full gap-0"):

        # Shotgun Tracker
        with ui.card().classes("no-shadow border-[1px] relative-top-left"):
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
            await table(data, classes="no-shadow w-full")


        # Current Standings
        with ui.card().classes("no-shadow border-[1px] col-span-3"):
            ui.label("Current Standings").classes("text-weight-bold underline text-xl text-center w-full")
            executable = select(
                Team.standing,
                Team.team_name,
                Team.display_name.label("Owner"),
                Team.wins,
                Team.losses,
                Team.points_for,
                Team.points_against,
                (func.substr(Team.streak_type, 1, 1) + cast(Team.streak_length, String)).label("Streak"),
            ).where(
                Team.year == datetime.now().year
            ).order_by(
                Team.standing
            )

            data = await query_data(executable)
            await table(data, classes="no-shadow border-[1px] w-full")

        # Highlighted Owners
        for role in CARD_INFOS:
            await owner_card(role)
