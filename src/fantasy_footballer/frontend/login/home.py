"""
Module to handle the login page and authentication of user.

Inspired by https://github.com/zauberzeug/nicegui/blob/main/examples/authentication/main.py.
"""

from typing import Optional

import bcrypt
from backend.db import DbManager
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to restrict access to all NiceGUI pages and redirects user to login page if not authenticated."""

    async def dispatch(self, request: Request, call_next):
        """Override dispatch method of parent class."""
        if not app.storage.user.get("authenticated", False):
            if not request.url.path.startswith("/_nicegui") and request.url.path not in {"/login"}:
                app.storage.user["referrer_path"] = request.url.path  # remember where the user wanted to go
                return RedirectResponse("/login")
        return await call_next(request)


@ui.page("/login")
def login() -> Optional[RedirectResponse]:
    """Login page with frontend elements and authentication mechanism."""
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        encoded_hash = user_results.get(username.value)
        if encoded_hash and bcrypt.checkpw(password=password.value.encode(), hashed_password=encoded_hash):
            app.storage.user.update({"username": username.value, "authenticated": True})
            ui.navigate.to("/")
        else:
            ui.notify("Wrong username or password", color="negative")

    user_results = DbManager.query("select user, hash from fantasy_footballer.main_seed_data.users", to_dict=True)
    user_results = {entry["user"]: entry["hash"].encode() for entry in user_results}

    if app.storage.user.get("authenticated", False):
        return RedirectResponse("/")
    with ui.card().classes("absolute-center"):
        username = ui.input("Username").on("keydown.enter", try_login)
        password = ui.input("Password", password=True, password_toggle_button=True).on("keydown.enter", try_login)
        ui.button("Log in", on_click=try_login)
    return None
