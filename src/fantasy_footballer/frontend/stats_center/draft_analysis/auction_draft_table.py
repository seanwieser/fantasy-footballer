"""Module for the Auction Draft Analysis table."""
from backend.db import DbManager
from frontend.utils import (VALID_POSITIONS, format_field_name,
                            get_draft_type_years, get_owner_names_by_year,
                            table)
from nicegui import ui


class AuctionDraftDropDownSelection:
    """Class for dropdown selection for Auction draft table."""

    DEFAULT = {
        "year": get_draft_type_years(is_auction=True)[-1],
        "owner": "ALL",
        "nominating_owner": "ALL",
        "position": "ALL",
        "keeper": "ALL",
    }

    def __init__(self):
        """Initialize DropDownSelection."""
        self.reset()

    def reset(self):
        """Reset all instance attributes to DEFAULT constant."""
        for attribute, value in AuctionDraftDropDownSelection.DEFAULT.items():
            setattr(self, attribute, value)
        auction_draft_data_table.refresh()

    def get_filter(self, field):
        """Return SQL boolean expression filtering 'field' parameter."""
        sql_filter = f"{field}::varchar='{getattr(self, field)}'"
        if getattr(self, field) == "ALL":
            return "1 = 1"

        return sql_filter


def filter_dropdown_button(selection: AuctionDraftDropDownSelection,
                           field: str,
                           field_options: list[str],
                           extra_format_funcs=None):
    """Generic dropdown button element with label above."""
    field_label = format_field_name(field, extra_format_funcs)
    with ui.column().classes("gap-1 mx-auto"):
        ui.label(field_label).classes("h-full mx-auto text-l text-weight-bold underline")
        with ui.dropdown_button(field_label, auto_close=True).classes("h-full mx-auto") as field_dropdown:
            field_dropdown.bind_text_from(selection, field)
            for field_option in ["ALL"] + field_options:
                ui.item(field_option,
                        on_click=lambda field_option=field_option: refresh_table(selection, field, field_option))


def filter_ui(selection: AuctionDraftDropDownSelection):
    """UI Element containing all user input options."""
    with ui.card().classes("w-full my-auto mx-auto"):
        with ui.row().classes("w-full gap-4 my-auto mx-auto"):
            filter_dropdown_button(selection, "year", [str(year) for year in get_draft_type_years(is_auction=True)])
            filter_dropdown_button(selection, "owner", get_owner_names_by_year())
            filter_dropdown_button(selection, "nominating_owner", get_owner_names_by_year())
            filter_dropdown_button(selection, "position", VALID_POSITIONS)
            filter_dropdown_button(selection, "keeper", ["true", "false"])


            ui.button("Reset Filter", on_click=selection.reset)


@ui.refreshable
def auction_draft_data_table(selection):
    """Data table displaying all draft data."""
    auction_draft_data_df = DbManager.query(f"""
        select
            year as "Year",
            owner as "Owner",
            team as "Team",
            nominating_owner as "Nominating Owner",
            keeper as "Keeper",
            player as "Player",
            position as "Position",
            round as "Round",
            round_pick as "Round Pick",
            bid_amount as "Bid Amount"
        from main_marts.auction_draft_table
        where   
            {selection.get_filter('year')} and
            {selection.get_filter('owner')} and
            {selection.get_filter('nominating_owner')} and
            {selection.get_filter('keeper')} and
            {selection.get_filter('position')}
        order by year desc, round, round_pick
    """)

    table(
        auction_draft_data_df,
        pagination=25,
        classes="mx-auto w-full",
        format_field_names=False,
        hidden_fields=[field for field, value in selection.__dict__.items() if value != "ALL"],
        slots=[{
            "name": "body-cell-Keeper",
            "template": r"""
                <q-td :props="props">
                    <q-icon :name="props.value.includes('true') ? 'done' : 'close'" 
                            :color="props.value.includes('true') ? 'green-3' : 'red-3'" />
                </q-td>"""
        }]
    )

def refresh_table(selection, field, value):
    """Refresh table with new selection."""
    setattr(selection, field, value)
    auction_draft_data_table.refresh(selection)


def auction_draft_table_and_dropdowns():
    """Dropdowns and Table for Players page."""
    selection = AuctionDraftDropDownSelection()
    filter_ui(selection)
    auction_draft_data_table(selection)
