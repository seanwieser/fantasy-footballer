"""Main entry point for the application."""

# pylint: disable=reimported

import os

from backend.db import DbManager
from frontend.login.home import AuthMiddleware
from frontend.owners.home import page
from frontend.owners.spotlight import page
from frontend.splash.home import page
from frontend.admin.home import page
from nicegui import app, ui

if __name__ in {"__main__", "__mp_main__"}:
    db_manager = DbManager()
    app.add_middleware(AuthMiddleware)
    app.on_startup(db_manager.setup)
    ui.run(title="Sco Chos",
       favicon=f"{os.getenv("MEDIA_DIR_PATH")}/favicons/football.ico",
       host="0.0.0.0",
       dark=None,
       storage_secret=os.getenv("STORAGE_SECRET"))
