from nicegui import ui
from frontend.utils import common_header


@ui.page("/gallery")
def page():  # pylint:disable=too-many-statements
    common_header()
    with ui.card_section().classes("mx-auto").classes("p-0 w-full h-full"):
        ui.html(
            f"""<div style="position:relative;padding-top:56.25%;"><iframe src="https://iframe.mediadelivery.net/embed/366287/9ad736fe-b905-43fa-a4d7-1b8cf5e4facd?autoplay=false&loop=false&muted=false&preload=false&responsive=true" loading="lazy" style="border:0;position:absolute;top:0;height:100%;width:100%;" allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture;" allowfullscreen="true"></iframe></div>""")
