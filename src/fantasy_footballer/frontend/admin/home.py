"""Module for Admin page."""

from multiprocessing import Manager

from backend.db import DbManager
from frontend.utils import common_header, get_valid_years
from nicegui import app, run, ui


@ui.page("/admin")
async def page():
    """Admin page to manually execute backend actions from the frontend."""
    def update_progressbars():
        fetch_progressbar.set_value(fetch_queue.get() if not fetch_queue.empty() else fetch_progressbar.value)
        refresh_progressbar.set_value(refresh_queue.get() if not refresh_queue.empty() else refresh_progressbar.value)

    async def async_fetch_data(years, source_tables):
        # Need a better way to repr the source tables mapping
        tables_by_source = {}
        for source_table in source_tables:
            source, table = [el.strip() for el in source_table.split(":")]
            if tables_by_source.get(source, False):
                tables_by_source[source].append(table)
            else:
                tables_by_source[source] = [table]

        for source, tables in tables_by_source.items():
            await run.cpu_bound(DbManager.fetch_data, years, source, tables, fetch_queue)

    async def async_refresh_data(sources):
        await run.cpu_bound(DbManager.refresh_db, sources, refresh_queue)

    common_header()

    ui.timer(1, callback=update_progressbars)

    source_info = DbManager.get_all_tables_by_source()

    # Fetch components
    options = []
    for source_name, table_names in source_info.items():
        for table_name in table_names:
            options.append(f"{source_name}: {table_name}") # Need a better way to repr the source tables mapping
    with ui.row():
        source_table_selections = ui.select(options, value=None, multiple=True, clearable=True)
        year_selections = ui.select(get_valid_years(), value=None, multiple=True, clearable=True)
    fetch_queue = Manager().Queue()
    ui.button("Fetch", on_click=lambda: async_fetch_data(year_selections.value, source_table_selections.value))
    fetch_progressbar = ui.linear_progress(value=0).props("instant-feedback")
    ui.separator()

    # Refresh components
    refresh_queue = Manager().Queue()
    source_selections = ui.select(list(source_info.keys()), value=None, multiple=True, clearable=True)
    ui.button("Refresh Data", on_click=lambda: async_refresh_data(source_selections))
    refresh_progressbar = ui.linear_progress(value=0).props("instant-feedback")
    ui.separator()

    ui.button("Shutdown", on_click=app.shutdown)
