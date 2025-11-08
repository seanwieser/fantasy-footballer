"""Module for Admin page to allow backend actions to be executed from frontend."""

import logging
import multiprocessing
from queue import Empty

from backend.db import DbManager
from frontend.utils import common_header, get_valid_years
from nicegui import app, run, ui


class LogElementHandler(logging.Handler):
    """A logging handler that emits messages to a log element."""

    def __init__(self, element: ui.log, level: int = logging.NOTSET) -> None:
        self.element = element
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        """Push formatted record to log element."""
        try:
            msg = self.format(record)
            self.element.push(msg)
        except Exception: # pylint: disable=broad-exception-caught
            self.handleError(record)

async def fetch_data_from_sources_ui(source_info, queue):
    """UI for fetching data from source and writing to cloud storage."""
    async def async_fetch_data_from_sources(years, source_tables, admin_queue):
        # Need a better way to repr the source tables mapping
        tables_by_source = {}
        for source_table in source_tables:
            source, table = [el.strip() for el in source_table.split(":")]
            if tables_by_source.get(source, False):
                tables_by_source[source].append(table)
            else:
                tables_by_source[source] = [table]

        for source, tables in tables_by_source.items():
            await run.cpu_bound(DbManager.fetch_data_from_sources, years, source, tables, admin_queue)

    options = []
    for source_name, table_names in source_info.items():
        for table_name in table_names:
            options.append(f"{source_name}: {table_name}") # Need a better way to repr the source tables mapping
    with ui.row():
        source_table_selections = ui.select(options, value=None, multiple=True, clearable=True)
        year_selections = ui.select(get_valid_years(), value=None, multiple=True, clearable=True)
    ui.button("Fetch data from source",
              on_click=lambda: async_fetch_data_from_sources(year_selections.value,
                                                             source_table_selections.value,
                                                             queue)
              )
    ui.separator()

async def async_ingest_raw_data_from_cloud(sources, queue):
    """Async function to ingest raw data from cloud."""
    await run.cpu_bound(DbManager.ingest_raw_data_from_cloud, sources, queue)

async def async_transform(queue):
    """Async function to run dbt."""
    await run.cpu_bound(DbManager.run_dbt, "build", queue)

def access_control_ui():
    """UI for adding users to the authentication system."""
    with ui.row():
        username_input = ui.input("Username", placeholder="username")
        password_input = ui.input("Password", placeholder="password", password=True, password_toggle_button=True)
    ui.button("Add User", on_click=lambda: DbManager.add_user(username_input.value, password_input.value))
    ui.separator()

def update_log(queue, log_element):
    """Update log element with items in queue."""
    items = []
    while not queue.empty():
        items.append(queue.get())
    message = "\n".join(items)
    log_element.push(message)

def clear_log(queue, log_element):
    """Empty the queue and log element."""
    while True:
        try:
            queue.get(block=False)
        except Empty:
            break  # Exit loop when the queue is empty
    log_element.clear()

@ui.page("/admin")
async def page():
    """Admin page to manually execute backend actions from the frontend."""
    common_header()

    admin_queue = multiprocessing.Manager().Queue()
    admin_log = ui.log()

    ui.timer(1.0, lambda: update_log(admin_queue, admin_log))

    source_info = DbManager.get_all_tables_by_source()
    await fetch_data_from_sources_ui(source_info, admin_queue)

    # Ingest raw data UI
    source_selections = ui.select(list(source_info.keys()), value=None, multiple=True, clearable=True)
    ui.button("Ingest raw data from cloud",
              on_click=lambda: async_ingest_raw_data_from_cloud(source_selections.value, admin_queue))
    ui.separator()

    # Transform UI
    ui.button("Transform", on_click=lambda: async_transform(admin_queue))  # pylint: disable=unnecessary-lambda
    ui.separator()
    access_control_ui()

    with ui.row():
        ui.button("Clear Log", on_click=lambda: clear_log(admin_queue, admin_log))
        ui.button("Shutdown", on_click=app.shutdown)
