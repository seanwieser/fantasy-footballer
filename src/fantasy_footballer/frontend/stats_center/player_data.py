"""Module for the Player Data page."""
from fantasy_footballer.frontend.utils import common_header
from frontend.utils import common_header, get_years, get_current_year
from nicegui import ui
from backend.db import DbManager
from inflection import humanize

class DropDownSelection:
    """Class for dropdown selection for Players table."""

    def __init__(self, year=None, position=None):
        """Initialize DropDownSelection."""
        self.year = year
        self.position = position

    def valid(self):
        """Check if year and position are valid."""
        return all([self.year, self.position])

    def set(self, year, position):
        """Set year and position."""
        if year:
            self.year = year
        if position:
            self.position = position

def filter_ui():
    with ui.card().classes('w-full'):
        ui.label('Fantasy Football Stats Dashboard').classes('text-2xl font-bold mb-4')

        all_owners = DbManager.query("select owner_name ")
        # Filter form
        with ui.card().classes('w-full mb-4'):
            ui.label('Filters').classes('text-lg font-semibold mb-2')

            with ui.row().classes('w-full gap-4'):
                with ui.column():
                    ui.label('Owner(s)')
                    owner_select = ui.select(
                        all_owners,
                        multiple=True,
                        value=[],
                        on_change=lambda e: (selected_owners.clear(), selected_owners.extend(e.value))
                    ).classes('w-40')

                with ui.column():
                    ui.label('Year(s)')
                    year_select = ui.select(
                        all_years,
                        multiple=True,
                        value=[],
                        on_change=lambda e: (selected_years.clear(), selected_years.extend(e.value))
                    ).classes('w-40')

                with ui.column():
                    ui.label('NFL Team(s)')
                    team_select = ui.select(
                        all_teams,
                        multiple=True,
                        value=[],
                        on_change=lambda e: (selected_teams.clear(), selected_teams.extend(e.value))
                    ).classes('w-40')

                with ui.column():
                    ui.label('Position(s)')
                    position_select = ui.select(
                        all_positions,
                        multiple=True,
                        value=[],
                        on_change=lambda e: (selected_positions.clear(), selected_positions.extend(e.value))
                    ).classes('w-40')

            with ui.row().classes('mt-4 gap-2'):
                ui.button('Apply Filters', on_click=update_table, color='primary')
                ui.button('Reset', on_click=reset_filters, color='secondary')


@ui.refreshable
def player_data_table(selection):
    """Table of players."""
    if selection.valid():
        where_clause = f""
        rows = DbManager.query(f"""
            select *
            from main_staging.stg_s001__players
            where year = {selection.year} and position_slot = {selection.position}
        """, to_dict=True)
        columns = []
        table_fields = [
            "player_key", "name", "position_slot", "position_rank", "pro_team", "total_points"
        ]
        for field in table_fields:
            col_dict = {
                "name": field,
                "label": humanize(field),
                "field": field,
                "sortable": True
            }
            if field == "player_key":
                col_dict["classes"] = "hidden"
                col_dict["headerClasses"] = "hidden"
            columns.append(col_dict)
        rows = [{k: v
                 for k, v in row.items() if k in table_fields} for row in rows]
        rows_ordered = sorted(rows,
                              key=lambda x: x["total_points"],
                              reverse=True)

        with ui.table(columns=columns,
                      rows=rows_ordered,
                      row_key="name",
                      pagination=25).classes("w-full").props("selection=single") as table:
            table.on("selection", lambda e: ui.notify(e.args))


def refresh_table(selection, year=None, position=None):
    """Refresh table with new year and position."""
    selection.set(year, position)
    player_data_table.refresh(selection)


def players_table_and_dropdowns():
    """Dropdowns and Table for Players page."""
    positions = DbManager.query("select distinct position_slot from main_staging.stg_s001__players")
    selection = DropDownSelection(get_current_year(), max(positions))
    with ui.row():
        with ui.dropdown_button("Year", auto_close=True) as year_dropdown:
            year_dropdown.bind_text_from(selection, "year")
            for year in get_years():
                ui.item(str(year),
                        on_click=lambda year=year: refresh_table(selection,
                                                                 year=year))

        with ui.dropdown_button("Position",
                                auto_close=True) as position_dropdown:
            position_dropdown.bind_text_from(selection, "position")
            for position in positions:
                ui.item(position,
                        on_click=lambda position=position: refresh_table(
                            selection, position=position))
    player_data_table(selection)

@ui.page("/stats_center/player_data")
def page():
    """Players page."""
    common_header()
    ui.label("Coming Soon...")
    players_table_and_dropdowns()


#
# # Get unique values for filters
# all_owners = sorted(df['Owner'].unique().tolist())
# all_years = sorted(df['Year'].unique().tolist())
# all_teams = sorted(df['NFL Team'].unique().tolist())
# all_positions = sorted(df['Position'].unique().tolist())
#
#
# @ui.page("/stats_center/player_data")
# def page():
#     common_header()
#     # Store selected filters
#     selected_owners = []
#     selected_years = []
#     selected_teams = []
#     selected_positions = []
#
#     def filter_data():
#         """Filter the dataframe based on selected criteria"""
#         filtered = df.copy()
#
#         if selected_owners:
#             filtered = filtered[filtered['Owner'].isin(selected_owners)]
#         if selected_years:
#             filtered = filtered[filtered['Year'].isin(selected_years)]
#         if selected_teams:
#             filtered = filtered[filtered['NFL Team'].isin(selected_teams)]
#         if selected_positions:
#             filtered = filtered[filtered['Position'].isin(selected_positions)]
#
#         return filtered
#
#     def update_table():
#         """Update the table with filtered data"""
#         filtered_df = filter_data()
#         table.options.rowData = filtered_df.to_dict('records')
#         table.update()
#         stats_label.set_text(f'Showing {len(filtered_df)} of {len(df)} records')
#
#     def reset_filters():
#         """Clear all filters"""
#         selected_owners.clear()
#         selected_years.clear()
#         selected_teams.clear()
#         selected_positions.clear()
#
#         owner_select.set_value([])
#         year_select.set_value([])
#         team_select.set_value([])
#         position_select.set_value([])
#
#         update_table()
#
#     # Create the UI
#     ui.page_title('Fantasy Football Stats')
#
#     with ui.card().classes('w-full'):
#         ui.label('Fantasy Football Stats Dashboard').classes('text-2xl font-bold mb-4')
#
#         # Filter form
#         with ui.card().classes('w-full mb-4'):
#             ui.label('Filters').classes('text-lg font-semibold mb-2')
#
#             with ui.row().classes('w-full gap-4'):
#                 with ui.column():
#                     ui.label('Owner(s)')
#                     owner_select = ui.select(
#                         all_owners,
#                         multiple=True,
#                         value=[],
#                         on_change=lambda e: (selected_owners.clear(), selected_owners.extend(e.value))
#                     ).classes('w-40')
#
#                 with ui.column():
#                     ui.label('Year(s)')
#                     year_select = ui.select(
#                         all_years,
#                         multiple=True,
#                         value=[],
#                         on_change=lambda e: (selected_years.clear(), selected_years.extend(e.value))
#                     ).classes('w-40')
#
#                 with ui.column():
#                     ui.label('NFL Team(s)')
#                     team_select = ui.select(
#                         all_teams,
#                         multiple=True,
#                         value=[],
#                         on_change=lambda e: (selected_teams.clear(), selected_teams.extend(e.value))
#                     ).classes('w-40')
#
#                 with ui.column():
#                     ui.label('Position(s)')
#                     position_select = ui.select(
#                         all_positions,
#                         multiple=True,
#                         value=[],
#                         on_change=lambda e: (selected_positions.clear(), selected_positions.extend(e.value))
#                     ).classes('w-40')
#
#             with ui.row().classes('mt-4 gap-2'):
#                 ui.button('Apply Filters', on_click=update_table, color='primary')
#                 ui.button('Reset', on_click=reset_filters, color='secondary')
#
#         # Stats summary
#         stats_label = ui.label(f'Showing {len(df)} of {len(df)} records').classes('text-sm text-gray-600 mb-2')
#
#         # Data table
#         table = ui.aggrid({
#             'columnDefs': [
#                 {'field': 'Owner', 'sortable': True, 'filter': True},
#                 {'field': 'Year', 'sortable': True, 'filter': True},
#                 {'field': 'Player', 'sortable': True, 'filter': True},
#                 {'field': 'NFL Team', 'sortable': True, 'filter': True},
#                 {'field': 'Position', 'sortable': True, 'filter': True},
#                 {'field': 'Points', 'sortable': True, 'filter': True},
#                 {'field': 'TDs', 'sortable': True, 'filter': True},
#             ],
#             'rowData': df.to_dict('records'),
#             'defaultColDef': {'flex': 1, 'minWidth': 100},
#         }).classes('w-full h-96')