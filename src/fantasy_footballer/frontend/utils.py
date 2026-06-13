"""Module contains utility functions for the marts."""
import datetime

from backend.db import DbManager
from inflection import titleize
from nicegui import app, context, ui
from pandas import DataFrame

START_YEAR = 2018
VALID_POSITIONS = ["QB", "RB", "WR", "TE", "D/ST", "K"]

# Highlight section -> Quasar color + medal emoji by podium rank. Shared by the League
# Highlights page and the owner-spotlight Highlights card so the visual language stays in sync.
SECTION_COLORS = {"Scoring": "blue", "Clutch": "red", "Matchups": "orange", "Shotgun": "green",
                  "Record": "purple", "Postseason": "teal", "Head to Head": "cyan", "The Rivalry": "pink",
                  "Transactions": "indigo", "Lineups": "amber", "Luck": "yellow",
                  # Glossary-only categories (don't co-occur with the highlight sections above).
                  "General": "blue-grey", "Roster": "cyan", "Draft": "purple", "Schedule": "grey"}
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

def medal(rank):
    """Medal emoji for a top-3 rank, else a plain numbered label (e.g. '4.')."""
    return MEDALS.get(rank, f"{rank}.")

def get_valid_years() -> list[int]:
    """Get all years that fantasy data is available for."""
    return list(range(START_YEAR, datetime.datetime.now().year + 1))

def get_years_by_owner_id(owner_id: str = None) -> list[str]:
    """Get all years that have fantasy data (by owner_id if passed)."""
    all_years_by_owner = DbManager.query("select * from main_marts.owner_year_map", to_dict=True)
    if owner_id:
        return list({row["year"] for row in all_years_by_owner if row["owner_id"] == int(owner_id)})
    return list({row["year"] for row in all_years_by_owner})

def get_draftpicks_rounds() -> list[str]:
    """Get all auction round values in the snake draft table."""
    round_nums = DbManager.query("select round from main_marts.snake_draft_table order by round", to_dict=True)
    return list({row["round"] for row in round_nums})

def get_draftpicks_round_picks() -> list[str]:
    """Get all auction round pick values in the snake draft table."""
    round_picks_sql = "select round_pick from main_marts.snake_draft_table order by round_pick"
    round_nums = DbManager.query(round_picks_sql, to_dict=True)
    return list({row["round_pick"] for row in round_nums})

def get_draft_type_years(is_auction: bool):
    """Get years for each draft type (auction/snake)."""
    table_name = "snake_draft_table"
    if is_auction:
        table_name = "auction_draft_table"

    years = DbManager.query(f"select distinct year from main_marts.{table_name} order by year", to_dict=True)
    return [row["year"] for row in years]

def get_owner_names_by_year(year: int = None) -> list[str]:
    """Get all owner names (by year if passed)."""
    all_owners_by_year = DbManager.query("""
        select *
        from main_marts.owner_year_map
        order by owner_name""", to_dict=True)
    if year:
        return sorted(list({row["owner_name"] for row in all_owners_by_year if row["year"] == int(year)}))
    return sorted(list({row["owner_name"] for row in all_owners_by_year}))

def get_owners_by_year(year: int) -> list[dict]:
    """Get owners (`owner_id`, `owner_name`) who fielded a team in a given year, sorted by name."""
    owners = DbManager.query(
        f"select owner_id, owner_name from main_marts.owner_year_map "
        f"where year = {int(year)} order by owner_name", to_dict=True)
    return owners

def get_nfl_teams():
    """Get all NFL Teams."""
    all_nfl_teams = DbManager.query("select nfl_team from main_marts.nfl_teams", to_dict=True)
    return sorted(list({row["nfl_team"] for row in all_nfl_teams}))

def get_current_year() -> int:
    """Get the latest year with fantasy data."""
    return [row["year"] for row in DbManager.query("select * from main_marts.current_year", to_dict=True)][0]

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

def get_access_level() -> int:
    """Highest page access level the current user may see (public=0, member=1, admin=2)."""
    username = app.storage.user.get("username")
    if username == "admin":
        return 2
    if username == "public":
        return 0
    return 1


def common_header() -> None:
    """Header: home + logout (+ shutdown for admins). Section navigation lives on the splash hub."""
    current_page = context.client.page.path.replace("/", "")
    with ui.header().classes(replace="row items-center"):
        home_color = "red" if current_page == "" else "primary"
        ui.button(on_click=lambda: ui.navigate.to("/"), icon="home").props(f"square color={home_color}")
        ui.space()
        if get_access_level() >= 2:
            ui.button(on_click=app.shutdown, icon="power_settings_new").props("square color=negative")
        ui.button(on_click=logout, icon="logout").props("square color=primary")

def glossary_link(slug: str, icon: str = "menu_book", size: str = "1rem", classes: str = "") -> None:
    """
    Render a small clickable icon that deep-links to a term's glossary entry (/glossary#<slug>).

    Used wherever a metric/term wants to point at its canonical definition. No-op when slug is falsy,
    so callers can pass a nullable glossary_slug straight through.
    """
    if not slug:
        return
    icon_el = ui.icon(icon, size=size).classes(f"cursor-pointer opacity-40 hover:opacity-90 {classes}")
    icon_el.on("click", lambda: ui.navigate.to(f"/glossary#{slug}"))
    icon_el.tooltip("Open in glossary")

def section_tile(label: str, icon: str, icon_color: str, route: str) -> None:
    """Clickable navigation tile (icon + label) linking to a section route. The splash hub's tile."""
    with ui.card() \
            .classes("w-full h-full p-5 gap-2 items-center justify-center "
                     "hover:shadow-lg transition-shadow cursor-pointer") \
            .on("click", lambda: ui.navigate.to(route)):
        ui.icon(icon, size="3rem", color=f"{icon_color}-6").classes("mx-auto")
        ui.label(label).classes("text-lg font-semibold text-center leading-tight mx-auto")

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
