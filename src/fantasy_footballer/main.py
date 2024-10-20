"""Main entry point for the application."""

# pylint: disable=reimported

from backend.db_init import DbInit
from backend.io_utils import MEDIA_PATH_TEMPLATE
from frontend.owners.home import page
from frontend.owners.spotlight import page
from frontend.splash.home import page
from nicegui import app, ui

app.on_startup(DbInit.init_tables)
ui.run(title="Sco Chos",
       favicon=MEDIA_PATH_TEMPLATE.substitute(sub_path="favicons/football",
                                              file_name="favicon.ico"),
       dark=None)
