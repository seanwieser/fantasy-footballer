"""Module contains utility functions for the marts."""
import datetime
import os

from backend.db import DbManager
from inflection import humanize
from nicegui import app, context, elements, ui
from pandas import DataFrame

START_YEAR = 2018
PAGES = ["owners", "admin"]

def get_valid_years() -> list[int]:
    """Get all years that fantasy data is available for."""
    return list(range(START_YEAR, datetime.datetime.now().year + 1))

def get_years() -> list[str]:
    """Get all years that have fantasy data."""
    return [row["year"] for row in DbManager.query("select * from main_utilities.all_years", to_dict=True)]

def get_current_year() -> int:
    """Get the latest year with fantasy data."""
    return [row["this"] for row in DbManager.query("select * from main_utilities.current_year", to_dict=True)][0]

def owner_id_to_owner_name(owner_id: str) -> str:
    """Return owner name given an owner id."""
    owner_name_sql = f"select * from main_seed_data.owner_names where owner_id == {owner_id}"
    return DbManager.query(owner_name_sql, to_dict=True)[0]["owner_name"]

def image_path_to_owner_id(image_path: str) -> str:
    """Return owner id given an image_path."""
    return image_path.rsplit("/", 1)[-1].replace(".jpg", "")

def image_path_to_owner_name(image_path: str) -> str:
    """Return owner name given an image_path."""
    owner_id = image_path_to_owner_id(image_path)
    return owner_id_to_owner_name(owner_id)

def logout() -> None:
    """Utility method to clear user authentication and redirect to login page."""
    app.storage.user.clear()
    ui.navigate.to("/login")

def common_header() -> None:
    """Header that is common for all pages."""
    current_page = context.client.page.path.replace("/", "")
    valid_pages = PAGES
    if app.storage.user.get("username") != "admin":
        valid_pages = [page for page in valid_pages if page != "admin"]

    with ui.header().classes(replace="row items-center"):
        color = "red" if current_page == "" else "primary"
        ui.button(on_click=lambda: ui.navigate.to("/"), icon="home").props(f"square color={color}")
        for page in valid_pages:
            color = "red" if page == current_page else "primary"
            ui.button(humanize(page),
                      on_click=lambda page=page: ui.navigate.to(f"/{page}")
                      ).props(f"square color={color}")
        ui.button(on_click=logout, icon="logout").props("square color=primary")

# pylint: disable=too-many-arguments,too-many-positional-arguments
def table(data_df: DataFrame,
          title: str="",
          classes: str="",
          props: str="",
          not_sortable: bool=None,
          align: str="center") -> ui.table:
    """Create a standard table element."""
    if title:
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label(title).classes("text-weight-bold underline text-xl text-center")
            tab = ui.table.from_pandas(data_df).classes(classes).props(props)
    else:
        tab = ui.table.from_pandas(data_df).classes(classes).props(props)

    not_sortable = not_sortable or []
    for col in tab.columns:
        col["sortable"] = col["name"] not in not_sortable and not_sortable != "all"
        col["align"] = align

    return tab
