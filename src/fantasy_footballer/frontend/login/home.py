"""
Module to handle the login page and authentication of user.

Inspired by https://github.com/zauberzeug/nicegui/blob/main/examples/authentication/main.py.
"""

import json
import os
from typing import Optional

import bcrypt
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from starlette.middleware.base import BaseHTTPMiddleware

unrestricted_page_routes = {"/login"}

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to restrict access to all NiceGUI pages and redirects user to login page if not authenticated."""

    async def dispatch(self, request: Request, call_next):
        """Override dispatch method of parent class."""
        if not app.storage.user.get("authenticated", False):
            if not request.url.path.startswith("/_nicegui") and request.url.path not in unrestricted_page_routes:
                app.storage.user["referrer_path"] = request.url.path  # remember where the user wanted to go
                return RedirectResponse("/login")
        return await call_next(request)


@ui.page("/login")
def login() -> Optional[RedirectResponse]:
    """Login page with frontend elements and authentication mechanism."""
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        hashes = {}
        with open(os.getenv("AUTH_USERS_PATH"), "r", encoding="utf-8") as users_file:
            for line in users_file:
                hashes.update(json.loads(line))

        encoded_password = password.value.encode()
        encoded_hash = hashes.get(username.value).encode()
        if bcrypt.checkpw(password=encoded_password, hashed_password=encoded_hash):
            app.storage.user.update({"username": username.value, "authenticated": True})
            ui.navigate.to(app.storage.user.get("referrer_path", "/"))  # go back to where the user wanted to go
        else:
            ui.notify("Wrong username or password", color="negative")

    if app.storage.user.get("authenticated", False):
        return RedirectResponse("/")
    with ui.card().classes("absolute-center"):
        username = ui.input("Username").on("keydown.enter", try_login)
        password = ui.input("Password", password=True, password_toggle_button=True).on("keydown.enter", try_login)
        ui.button("Log in", on_click=try_login)
    return None
