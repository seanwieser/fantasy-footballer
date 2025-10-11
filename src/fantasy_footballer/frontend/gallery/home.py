"""Module for Gallery page for users to view league related media."""
# pylint:disable=too-many-statements, disable=line-too-long
from frontend.utils import common_header
from nicegui import ui


@ui.page("/gallery")
def page():
    """Gallery Page to display media hosted by bunny cdn."""
    common_header()
    ui.label("Under Construction...")
    # with ui.card_section().classes("mx-auto").classes("p-0 w-full h-full"):
    #     ui.html(
    #         r"""
    #     <div style="position:relative;padding-top:56.25%;">
    #     <iframe
    #         src=""
    #         loading="lazy"
    #         style="border:0;position:absolute;top:0;height:100%;width:100%;"
    #         allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture;"
    #         allowfullscreen="true"
    #     >
    #     </iframe>
    #     </div>""")
