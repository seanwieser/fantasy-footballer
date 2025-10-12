"""Module containing all pages within the Stats Center."""

from frontend.utils import common_header
from nicegui import ui


def stats_center_card(label, icon, icon_color):
    """Reusable ui component for the Stats Center subpages."""
    with ui.card() \
            .classes("p-6 hover:shadow-lg transition-shadow cursor-pointer") \
            .on("click", lambda: ui.navigate.to(f"/stats_center/{label.replace(" ", "_").lower()}")):
        ui.icon(icon, size="5rem", color=f"{icon_color}-6").classes("mx-auto")
        ui.label(label).classes("text-3xl font-semibold mb-1 mx-auto")

@ui.page("/stats_center")
def page():
    """Landing page for the Stats Center."""
    common_header()

    with ui.column().classes("w-full items-center px-8 py-16 no-shadow"):
        with ui.column().classes("max-w-7xl w-full gap-8"):
            with ui.grid(columns=3).classes("w-full gap-6"):
                stats_center_card(label="Postseason History", icon="history", icon_color="yellow")
                stats_center_card(label="H2H Dashboard", icon="sym_s_swords", icon_color="red")
                stats_center_card(label="League Highlights", icon="sym_s_star", icon_color="orange")
                stats_center_card(label="Player Data", icon="sym_s_data_loss_prevention", icon_color="blue")
                stats_center_card(label="Draft Analysis", icon="price_check", icon_color="green")
