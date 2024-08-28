"""Module contains utility functions for the frontend."""

import json

from backend.engine import async_session
from inflection import humanize
from nicegui import ui, context

PAGES = ["owners", "players", "leaderboard"]


class WindowSize:
    """Class for storing window size."""

    def __init__(self, width=0, height=0):
        """Initialize WindowSize."""
        self.width = width
        self.height = height

    def set_size(self, width, height):
        """Set the size of the window."""
        return WindowSize(width, height)

    def __repr__(self):
        """Return string representation of WindowSize."""
        return json.dumps({"width": self.width, "height": self.height})


def add_window_resize_event():
    """Add window resize event to the page."""
    ui.add_head_html("""
        <script>
        function emitSize() {
            emitEvent('resize', {
                width: document.body.offsetWidth,
                height: document.body.offsetHeight,
            });
        }
        window.onload = emitSize;
        window.onresize = emitSize;
        </script>
    """)
    return WindowSize()


def image_path_to_owner_name(image_path):
    """Convert image path to owner name."""
    return image_path.rsplit('/', 1)[-1].replace(".jpg", "")


async def query_data(executable):
    """Query database with executable and return all rows."""
    async with async_session() as session:
        async with session.begin():
            rows = await session.execute(executable)
    return rows.all()


def common_header():
    """Header that is common for all pages."""
    current_page = context.client.page.path.replace("/", "")
    with ui.header().classes(replace='row items-center'):
        color = "red" if current_page == "" else "primary"
        ui.button(on_click=lambda: ui.navigate.to("/"), icon='home').props(f"square color={color}")
        for page in PAGES:
            color = "red" if page == current_page else "primary"
            ui.button(
                humanize(page),
                on_click=lambda page=page: ui.navigate.to(f"/{page}")).props(f"square color={color}"
                )
