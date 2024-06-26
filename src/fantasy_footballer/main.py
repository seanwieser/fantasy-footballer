"""Main entry point for the application."""

from backend.db_init import DbInit
from backend.io_utils import MEDIA_PATH_TEMPLATE
from frontend.home.page import home_page
from frontend.leaderboard.page import leaderboard_page
from frontend.owners.page import owner_page, owners_page
from frontend.players.page import players_page
from nicegui import app, ui

app.on_startup(DbInit.init_tables)
ui.run(title="Sco Chos",
       favicon=MEDIA_PATH_TEMPLATE.substitute(sub_path="favicons/football",
                                              file_name="favicon.ico"),
       dark=None)
