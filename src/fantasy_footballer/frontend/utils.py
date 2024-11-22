"""Module contains utility functions for the marts."""

from backend.db import DbManager
from inflection import humanize
from nicegui import context, ui

PAGES = ["owners"]

def get_years() -> list[str]:
    """Get all years that have fantasy data."""
    return [row["year"] for row in DbManager.query("select * from main_utilities.all_years", to_dict=True)]

def owner_id_to_owner_name(owner_id: str) -> str:
    """Return owner name given an owner id."""
    owner_name_sql = f"select * from main_seed_data.owner_ids where owner_id == {owner_id}"
    return DbManager.query(owner_name_sql, to_dict=True)[0]["owner_name"]

def image_path_to_owner_id(image_path: str) -> str:
    """Return owner id given an image_path."""
    return image_path.rsplit("/", 1)[-1].replace(".jpg", "")

def image_path_to_owner_name(image_path: str) -> str:
    """Return owner name given an image_path."""
    owner_id = image_path_to_owner_id(image_path)
    return owner_id_to_owner_name(owner_id)


def common_header():
    """Header that is common for all pages."""
    current_page = context.client.page.path.replace("/", "")
    with ui.header().classes(replace="row items-center"):
        color = "red" if current_page == "" else "primary"
        ui.button(on_click=lambda: ui.navigate.to("/"), icon="home").props(f"square color={color}")
        for page in PAGES:
            color = "red" if page == current_page else "primary"
            ui.button(humanize(page),
                      on_click=lambda page=page: ui.navigate.to(f"/{page}")
                      ).props(f"square color={color}")


def table(data_df, title="", classes="", props="", not_sortable=None, align="center"): # pylint: disable=too-many-arguments,too-many-positional-arguments
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
