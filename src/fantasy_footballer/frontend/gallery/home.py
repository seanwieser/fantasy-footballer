# pylint:disable=too-many-statements, disable=line-too-long
from frontend.utils import common_header
from nicegui import ui


@ui.page("/gallery")
def page():
    common_header()
    with ui.card_section().classes("mx-auto").classes("p-0 w-full h-full"):
        ui.html(
            r"""
        <div style="position:relative;padding-top:56.25%;">
        <iframe 
            src="https://iframe.mediadelivery.net/embed/366287/9ad736fe-b905-43fa-a4d7-1b8cf5e4facd?autoplay=false&loop=false&muted=false&preload=false&responsive=true" 
            loading="lazy" 
            style="border:0;position:absolute;top:0;height:100%;width:100%;" 
            allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture;" 
            allowfullscreen="true"
        >
        </iframe>
        </div>""")
