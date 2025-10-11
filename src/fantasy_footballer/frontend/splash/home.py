"""Home page for the marts."""

from backend.db import DbManager
from frontend.utils import common_header, table
from nicegui import ui

# def owner_card(role: str):
#     """Elements to highlight key owners on the splash page."""
#     with ui.card().tight().classes("no-shadow border-[1px]"):
#         with ui.card_section().classes("mx-auto").classes("p-0"):
#             ui.label(titleize(role)).classes("text-weight-bold underline text-xl")
#         image_path = f"resources/media/owners/{CARD_INFOS[role]['owner_id']}.jpg"
#         ui.image(image_path).props("fit=scale-down")
#         with ui.card_section().classes("mx-auto p-0"):
#             with ui.row().classes("place-content-center text-weight-bold underline text-base"):
#                 owner_id = image_path_to_owner_id(image_path)
#                 ui.link(owner_id, f"/owners/{owner_id}")
#             with ui.row().classes("text-center italic"):
#                 ui.label(CARD_INFOS[role]["statement"])


@ui.page("/")
def page():
    """Home page."""
    common_header()
    with ui.grid(columns="1fr 1fr 1fr 1fr").classes("w-full gap-0"):

        # Shotgun Counter
        with ui.card().classes("no-shadow border-[1px] relative-top-left"):
            with ui.card_section().classes("mx-auto").classes("p-0 pt-2"):
                ui.label("Shotgun Counter").classes("text-weight-bold underline text-xl text-center")
            sql = "select * from fantasy_footballer.main_marts.current_shotgun_counter"
            standings_df = DbManager.query(sql)
            table(standings_df, classes="no-shadow w-full", not_sortable="all")


        # Current Standings
        with ui.card().classes("no-shadow border-[1px] col-span-3"):
            ui.label("Current Standings").classes("text-weight-bold underline text-xl text-center w-full")
            sql = "select * from fantasy_footballer.main_marts.current_standings"
            standings_df = DbManager.query(sql)
            table(standings_df, classes="no-shadow border-[1px] w-full", not_sortable=["Name", "Owner"])
