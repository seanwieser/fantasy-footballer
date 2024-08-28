"""Home page for the frontend."""

from frontend.utils import common_header
from nicegui import app, ui
from inflection import titleize, humanize
from backend.io_utils import MEDIA_PATH_TEMPLATE

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
    "current_winner": {
        "name": "aditya_sinha",
        "statement": """
        Same an quit most an. Admitting an mr disposing sportsmen. Tried on cause no spoil arise plate.
        """
    }
}


async def owner_card(role: str):
    with ui.card().tight().classes("no-shadow border-[0px]"):
        with ui.card_section().classes("mx-auto").classes("p-0"):
            with ui.row():
                ui.label(titleize(role)).classes("text-weight-bold underline text-xl")
        ui.image(MEDIA_PATH_TEMPLATE.substitute(sub_path="owners", file_name=f"{CARD_INFOS[role]['name']}.jpg")).props("fit=scale-down")
        with ui.card_section().classes("mx-auto p-0"):
            with ui.row().classes("place-content-center text-weight-bold underline text-base"):
                ui.link(titleize(CARD_INFOS[role]["name"]), f"/owners/{CARD_INFOS[role]['name']}")
            with ui.row().classes("text-center italic"):
                ui.label(CARD_INFOS[role]["statement"])


async def shotgun_table():
    columns = []
    for col in ["owner", "due", "completed"]:
        col_dict = {
            "name": col,
            "label": humanize(col),
            "field": col,
            "sortable": True
        }
        columns.append(col_dict)

    rows = [
        {"owner": "casey_magid", "due": "1", "completed": "1"},
        {"owner": "adam_barrett", "due": "1", "completed": "1"},
        {"owner": "aditya_sinha", "due": "1", "completed": "1"},
        {"owner": "casey_magid", "due": "1", "completed": "1"},

    ]
    ui.table(columns=columns, rows=rows).classes("no-shadow border-[0px]").props("dense")


async def current_leaderboard():
    columns = []
    for col in ["owner", "due", "completed"]:
        col_dict = {
            "name": col,
            "label": humanize(col),
            "field": col,
            "sortable": True
        }
        columns.append(col_dict)

    rows = [
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
    ui.table(columns=columns, rows=rows).classes("no-shadow border-[0px] w-full no-wrap")


@ui.page("/")
async def home_page():
    """Home page."""
    common_header()
    with ui.grid(columns=len(CARD_INFOS)).classes("gap-1 w-2/3 fixed-bottom-left pb-3"):
        for role, info in CARD_INFOS.items():
            await owner_card(role)
    with ui.card().classes("no-shadow border-[0px] relative-top-left"):
        with ui.card_section().classes("mx-auto").classes("p-0 pt-2"):
            ui.label("Shotgun Tracker").classes("text-weight-bold underline text-xl text-center")
        # with ui.scroll_area().classes("flex-auto"):
        await shotgun_table()
    with ui.right_drawer(fixed=True).style().props('width=500'):
        ui.label("Current Leaderboard").classes("text-weight-bold underline text-xl text-center")
        await current_leaderboard()
