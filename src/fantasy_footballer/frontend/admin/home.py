"""Module for Admin page to allow backend actions to be executed from frontend."""

from multiprocessing import Manager

from backend.db import DbManager
from frontend.utils import common_header, get_valid_years
from nicegui import app, run, ui


async def fetch_data_from_sources_ui(source_info):
    """UI for fetching data from source and writing to cloud storage."""
    async def async_fetch_data_from_sources(years, source_tables):
        # Need a better way to repr the source tables mapping
        tables_by_source = {}
        for source_table in source_tables:
            source, table = [el.strip() for el in source_table.split(":")]
            if tables_by_source.get(source, False):
                tables_by_source[source].append(table)
            else:
                tables_by_source[source] = [table]

        for source, tables in tables_by_source.items():
            await run.cpu_bound(DbManager.fetch_data_from_sources, years, source, tables, fetch_queue)

    fetch_progressbar = ui.linear_progress(value=0).props("instant-feedback")
    fetch_queue = Manager().Queue()

    options = []
    for source_name, table_names in source_info.items():
        for table_name in table_names:
            options.append(f"{source_name}: {table_name}") # Need a better way to repr the source tables mapping
    with ui.row():
        source_table_selections = ui.select(options, value=None, multiple=True, clearable=True)
        year_selections = ui.select(get_valid_years(), value=None, multiple=True, clearable=True)
    ui.button("Fetch data from source",
              on_click=lambda: async_fetch_data_from_sources(year_selections.value, source_table_selections.value)
              )
    ui.separator()

    return fetch_progressbar, fetch_queue

async def ingest_data_from_cloud_ui(source_info):
    """UI for refreshing data in database layer."""
    async def async_ingest_data_from_cloud(sources):
        refresh_progressbar.clear()
        await run.cpu_bound(DbManager.ingest_data_from_cloud, sources, refresh_queue)

    refresh_queue = Manager().Queue()
    refresh_progressbar = ui.linear_progress(value=0).props("instant-feedback")

    source_selections = ui.select(list(source_info.keys()), value=None, multiple=True, clearable=True)
    ui.button("Ingest raw data from cloud",
              on_click=lambda: async_ingest_data_from_cloud(source_selections.value))
    ui.separator()

    return refresh_progressbar, refresh_queue

async def transform_data_ui():
    """UI for refreshing data in database layer."""
    async def async_transform_data():
        refresh_progressbar.clear()
        await run.cpu_bound(DbManager.run_dbt)

    refresh_queue = Manager().Queue()
    refresh_progressbar = ui.linear_progress(value=0).props("instant-feedback")

    ui.button("Transform", on_click=lambda: async_transform_data)
    ui.separator()

    return refresh_progressbar, refresh_queue

def access_control_ui():
    """UI for adding users to the authentication system."""
    with ui.row():
        username_input = ui.input("Username", placeholder="username")
        password_input = ui.input("Password", placeholder="password", password=True, password_toggle_button=True)
    ui.button("Add User", on_click=lambda: DbManager.add_user(username_input.value, password_input.value))
    ui.separator()


@ui.page("/admin")
async def page():
    """Admin page to manually execute backend actions from the frontend."""
    def update_progressbars():
        fetch_progressbar.set_value(fetch_queue.get() if not fetch_queue.empty() else fetch_progressbar.value)
        ingest_progressbar.set_value(ingest_queue.get() if not ingest_queue.empty() else ingest_progressbar.value)
        transform_progressbar.set_value(
            transform_queue.get() if not transform_queue.empty() else transform_progressbar.value
        )

    common_header()
    ui.timer(1, callback=update_progressbars)

    source_info = DbManager.get_all_tables_by_source()
    fetch_progressbar, fetch_queue = await fetch_data_from_sources_ui(source_info)
    ingest_progressbar, ingest_queue = await ingest_data_from_cloud_ui(source_info)
    transform_progressbar, transform_queue = await transform_data_ui()
    access_control_ui()

    ui.button("Shutdown", on_click=app.shutdown)
