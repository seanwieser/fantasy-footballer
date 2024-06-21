from api.api import api_app
from fastapi import FastAPI
from nicegui import ui


def init(fastapi_app: FastAPI) -> None:

    @ui.page('/')
    def show():
        ui.label('Hellod, FastAPI!')
        ui.link("Link", "/leaderboard")

    ui.run_with(fastapi_app, storage_secret="")


init(api_app)
