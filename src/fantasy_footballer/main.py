"""Main entry point for the application."""

# pylint: disable=reimported

import os

from backend.db import DbManager
from frontend.owners.home import page
from frontend.owners.spotlight import page
from frontend.splash.home import page
from nicegui import app, ui

db_manager = DbManager()
app.on_startup(db_manager.setup)
ui.run(title="Sco Chos",
       favicon=f"{os.getenv("MEDIA_DIR_PATH")}/favicons/football.ico",
       host="0.0.0.0",
       dark=None)
