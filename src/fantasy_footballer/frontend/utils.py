"""Module contains utility functions for the frontend."""

import json

from backend.engine import async_session
from backend.models import Team
from inflection import humanize
from nicegui import context, ui
from sqlalchemy import select

PAGES = ["owners", "players"]

async def get_fantasy_years():
    """Get all years that have fantasy data."""
    year_results = await query_data(select(Team.year).distinct().order_by(Team.year))
    return [row["year"] for row in year_results]


def image_path_to_owner_name(image_path):
    """Convert image path to owner name."""
    return image_path.rsplit("/", 1)[-1].replace(".jpg", "")


async def query_data(executable):
    """Query database with executable and return all rows."""
    async with async_session() as session:
        async with session.begin():
            rows = await session.execute(executable)
    return [row._asdict() for row in rows.all()]


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


async def table(data, title="", classes="", props="", pagination=None):
    """Create a standard table element."""

    # Need to maintain order of fields that are in the data
    fields = []
    for row in data:
        for field in row:
            if field not in fields:
                fields.append(field)

    columns = []
    for col in fields:
        col_dict = {
            "name": col,
            "label": humanize(col),
            "field": col,
            "sortable": True
        }
        columns.append(col_dict)
    if title:
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label(title).classes("text-weight-bold underline text-xl text-center")
            return ui.table(columns=columns, rows=data, pagination=pagination).classes(classes).props(props)
    else:
        ui.table(columns=columns, rows=data, pagination=pagination).classes(classes).props(props)
