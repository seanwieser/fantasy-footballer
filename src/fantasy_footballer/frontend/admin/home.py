import os

from backend.db import DbManager
from frontend.utils import common_header, get_valid_years
from nicegui import ui, app, run
import datetime
from functools import partial
from multiprocessing import Manager, Queue

BACKUP_EXTENSIONS = ["jsonl", "ico", "duckdb", "jpg"]


@ui.page("/admin")
async def page():
    """Admin page to manually execute backend actions from the frontend."""
    async def fetch_data_w_progress_bar(years, source_tables):

        # Need a better way to repr the source tables mapping
        tables_by_source = {}
        for source_table in source_tables:
            source, table = [el.strip() for el in source_table.split(":")]
            if tables_by_source.get(source, False):
                tables_by_source[source].append(table)
            else:
                tables_by_source[source] = [table]

        for source, tables in tables_by_source.items():
            await run.cpu_bound(DbManager.fetch_data, years, source, tables, queue)

    common_header()

    queue = Manager().Queue()
    ui.timer(1, callback=lambda: progressbar.set_value(queue.get() if not queue.empty() else progressbar.value))

    # Need a better way to repr the source tables mapping
    options = []
    for source_name, table_names in DbManager.get_all_tables_by_source().items():
        for table_name in table_names:
            options.append(f"{source_name}: {table_name}")

    with ui.row():
        source_table_selections = ui.select(options, value=None, multiple=True, clearable=True)
        year_selections = ui.select(get_valid_years(), value=None, multiple=True, clearable=True)


    ui.button("Fetch", on_click=lambda: fetch_data_w_progress_bar(year_selections.value, source_table_selections.value))
    progressbar = ui.linear_progress(value=0).props("instant-feedback")

    ui.separator()
    ui.button("Shutdown", on_click=app.shutdown)
