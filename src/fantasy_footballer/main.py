"""Main entry point for the application."""

# pylint: disable=reimported,unused-import

import os

import argparse
from backend.db import DbManager
from frontend.admin import home
from frontend.gallery import home
from frontend.login.home import AuthMiddleware
from frontend.owner_history import home, spotlight
from frontend.splash import home
from frontend.stats_center import (draft_analysis, h2h_dashboard, home,
                                   league_highlights, player_data)
from nicegui import app, ui

if __name__ in {"__main__", "__mp_main__"}:
    parser = argparse.ArgumentParser(description='A simple program that greets the user.')
    parser.add_argument("--dev-mode", action="store_true")
    args = parser.parse_args()
    db_manager = DbManager(args.dev_mode)
    app.add_middleware(AuthMiddleware)
    app.on_startup(db_manager.setup)
    ui.run(title="Sco Chos",
           host="0.0.0.0",
           dark=None,
           storage_secret=os.getenv("STORAGE_SECRET"))
