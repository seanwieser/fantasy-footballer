"""Main entry point for the application."""

# pylint: disable=reimported,unused-import

import os

import click
from backend.db import DbManager
from frontend.admin import home
from frontend.gallery import home
from frontend.login.home import AuthMiddleware
from frontend.owner_history import home, spotlight
from frontend.splash import home
from frontend.stats_center import (draft_analysis, h2h_dashboard, home,
                                   league_highlights, player_data)
from nicegui import app, ui


@click.command()
@click.option("--dev-mode", is_flag=True)
def main(dev_mode: bool = False):
    db_manager = DbManager()
    app.add_middleware(AuthMiddleware)
    app.on_startup(lambda: db_manager.setup(dev_mode))
    ui.run(title="Sco Chos",
           host="0.0.0.0",
           dark=None,
           storage_secret=os.getenv("STORAGE_SECRET"))


if __name__ in {"__main__", "__mp_main__"}:
    main()
