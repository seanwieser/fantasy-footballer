"""Home page for the frontend."""

from frontend.utils import common_header
from nicegui import app, ui


@ui.page('/')
def home_page():
    """Home page."""
    common_header()
    ui.label('Home')
