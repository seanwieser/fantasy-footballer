"""Module for the Group Chat page — league iMessage engagement leaderboard (source s003)."""

from backend.db import DbManager
from frontend.utils import common_header, format_field_name, table
from nicegui import ui


def get_chat_years() -> list[str]:
    """Distinct years present in the chat leaderboard, newest first (empty until first extract)."""
    years = DbManager.query(
        "select distinct year from main_marts.chat_activity_leaderboard order by year desc", to_dict=True)
    return [str(row["year"]) for row in years]


class ChatDropDownSelection:
    """Class for dropdown selection for the group-chat leaderboard table."""

    @classmethod
    def defaults(cls):
        """Default selections, resolved at call time so there is no DB access at import."""
        chat_years = get_chat_years()
        return {"year": chat_years[0] if chat_years else "ALL"}

    def __init__(self):
        """Initialize DropDownSelection."""
        self.reset()

    def reset(self):
        """Reset all instance attributes to their defaults."""
        for attribute, value in self.defaults().items():
            setattr(self, attribute, value)
        chat_data_table.refresh()

    def get_filter(self, field):
        """Return SQL boolean expression filtering 'field' parameter."""
        if getattr(self, field) == "ALL":
            return "1 = 1"
        return f"{field}::varchar='{getattr(self, field)}'"


def filter_dropdown_button(selection: ChatDropDownSelection, field: str, field_options: list[str]):
    """Generic dropdown button element with label above."""
    field_label = format_field_name(field)
    with ui.column().classes("gap-1 mx-auto"):
        ui.label(field_label).classes("h-full mx-auto text-l text-weight-bold underline")
        with ui.dropdown_button(field_label, auto_close=True) as field_dropdown:
            field_dropdown.bind_text_from(selection, field)
            for field_option in ["ALL"] + field_options:
                ui.item(field_option,
                        on_click=lambda field_option=field_option: refresh_table(selection, field, field_option))


def filter_ui(selection: ChatDropDownSelection):
    """UI Element containing all user input options."""
    with ui.card().classes("w-full my-auto mx-auto"):
        with ui.row().classes("w-full gap-4 my-auto mx-auto"):
            filter_dropdown_button(selection, "year", get_chat_years())
            ui.button("Reset Filter", on_click=selection.reset)


@ui.refreshable
def chat_data_table(selection):
    """Data table displaying the group-chat engagement leaderboard."""
    chat_data_df = DbManager.query(f"""
        select
            year                as Year,
            owner_name          as "Owner",
            owner_id            as "Owner Id",
            message_count       as "Messages",
            avg_word_count      as "Avg Words",
            attachment_count    as "Attachments",
            reactions_received  as "Reactions Received",
            reactions_given     as "Reactions Given",
            share_of_chat_pct   as "Share %"
        from main_marts.chat_activity_leaderboard
        where {selection.get_filter('year')}
        order by message_count desc
    """)

    chat_table = table(chat_data_df,
          pagination=25,
          classes="mx-auto w-full cursor-pointer",
          format_field_names=False,
          hidden_fields=[field for field, value in selection.__dict__.items() if value != "ALL"] + ["Owner Id"],
    )
    chat_table.on("rowClick",
                  lambda event: ui.navigate.to(f"/owner_history/{event.args[1]['Owner Id']}/{event.args[1]['Year']}"))


def refresh_table(selection, field, value):
    """Refresh table with the newly selected filter value."""
    setattr(selection, field, value)
    chat_data_table.refresh(selection)


def chat_table_and_dropdowns():
    """Dropdowns and table for the Group Chat page."""
    selection = ChatDropDownSelection()
    filter_ui(selection)
    chat_data_table(selection)


@ui.page("/group_chat")
def page():
    """Group Chat page."""
    common_header()
    chat_table_and_dropdowns()
