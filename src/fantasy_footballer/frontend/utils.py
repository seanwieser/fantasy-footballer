"""Module contains utility functions for the marts."""
import datetime

from backend.db import DbManager
from inflection import humanize, titleize
from nicegui import app, context, ui
from pandas import DataFrame

START_YEAR = 2018
VALID_POSITIONS = ["QB", "RB", "WR", "TE", "FLEX", "D/ST", "K"]

def get_valid_years() -> list[int]:
    """Get all years that fantasy data is available for."""
    return list(range(START_YEAR, datetime.datetime.now().year + 1))

def get_years_by_owner_id(owner_id: str = None) -> list[str]:
    """Get all years that have fantasy data (by owner_id if passed)."""
    all_years_by_owner = DbManager.query("select * from main_utilities.owner_year_map", to_dict=True)
    if owner_id:
        return list({row["year"] for row in all_years_by_owner if row["owner_id"] == int(owner_id)})
    return list({row["year"] for row in all_years_by_owner})

def get_owner_names_by_year(year: int = None) -> list[str]:
    """Get all owner names (by year if passed)."""
    all_owners_by_year = DbManager.query("""
        select * 
        from main_utilities.owner_year_map 
        order by owner_name""", to_dict=True)
    if year:
        return sorted(list({row["owner_name"] for row in all_owners_by_year if row["year"] == int(year)}))
    return sorted(list({row["owner_name"] for row in all_owners_by_year}))

def get_nfl_teams():
    """Get all NFL Teams."""
    all_nfl_teams = DbManager.query("select nfl_team from main_utilities.nfl_teams", to_dict=True)
    return sorted(list({row["nfl_team"] for row in all_nfl_teams}))

def get_current_year() -> int:
    """Get the latest year with fantasy data."""
    return [row["this"] for row in DbManager.query("select * from main_utilities.current_year", to_dict=True)][0]

def owner_id_to_owner_name(owner_id: str) -> str:
    """Return owner name given an owner id."""
    owner_name_sql = f"select * from main_seed_data.owner_names where owner_id == {owner_id}"
    print(owner_id)
    print(DbManager.query(owner_name_sql, to_dict=True))
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
    page_by_access_level = {"owner_history": 0, "stats_center": 0, "gallery": 1, "admin": 2}
    username = app.storage.user.get("username")
    if username == "public":
        valid_pages = [page for page, access_level in page_by_access_level.items() if access_level == 0]
    elif username == "admin":
        valid_pages = [page for page, access_level in page_by_access_level.items() if access_level <= 2]
    else:
        valid_pages = [page for page, access_level in page_by_access_level.items() if access_level <= 1]

    current_page = context.client.page.path.replace("/", "")
    with ui.header().classes(replace="row items-center"):
        color = "red" if current_page == "" else "primary"
        ui.button(on_click=lambda: ui.navigate.to("/"), icon="home").props(f"square color={color}")
        for page in valid_pages:
            color = "red" if page == current_page else "primary"
            ui.button(humanize(page),
                      on_click=lambda page=page: ui.navigate.to(f"/{page}")
                      ).props(f"square color={color}")
        ui.button(on_click=logout, icon="logout").props("square color=primary")

def format_field_name(field_name, extra_funcs=None):
    """Format field names to be displayed on UI (applying extra functions if passed)."""
    formatted_field_name = titleize(field_name.replace('_', ' '))

    extra_funcs = extra_funcs or []
    for func in extra_funcs:
        formatted_field_name = func(formatted_field_name)

    return formatted_field_name

# pylint: disable=too-many-arguments,too-many-positional-arguments
def table(data_df: DataFrame,
          title: str="",
          classes: str="",
          props: str="",
          format_field_names: bool = True,
          hidden_fields: list[str] = None,
          not_sortable: list[str] = None,
          align: str= "center",
          slots: list[str] = None,
          pagination: int = None) -> ui.table:
    """Create a standard table element."""
    if format_field_names:
        data_df = data_df.rename(columns=format_field_name)

    if title:
        with ui.card().classes("no-shadow border-[0px] w-full"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label(title).classes("text-weight-bold underline text-xl text-center")
            tab = ui.table.from_pandas(data_df, pagination=pagination).classes(classes).props(props)
    else:
        tab = ui.table.from_pandas(data_df, pagination=pagination).classes(classes).props(props)

    slots = slots or []
    for slot in slots:
        tab.add_slot(**slot)

    not_sortable = not_sortable or []
    hidden_fields = [format_field_name(field) for field in hidden_fields or []]
    for col in tab.columns:
        col["sortable"] = col["name"] not in not_sortable and not_sortable != "all"
        col['classes'] = '' if col["name"] not in hidden_fields else 'hidden'
        col['headerClasses'] = '' if col["name"] not in hidden_fields else 'hidden'
        col["align"] = align
    tab.update()

    return tab
