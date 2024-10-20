"""Spotlight page for each owner."""
from datetime import datetime
from string import Template

from backend.io_utils import MEDIA_PATH_TEMPLATE
from frontend.utils import (common_header, get_fantasy_years,
                            image_path_to_owner_name, query_data, table)
from inflection import titleize
from nicegui import ui
from sqlalchemy import text

SEASON_OVERVIEW_SQL = Template("""
            select 
                wins || '-' || losses as record,
                points_for,
                points_against,
                acquisitions,
                100-acquisition_budget_spent as budget,
                standing,
                trades,
                substr(streak_type, 1, 1) || streak_length as streak
            from teams
            where team_key = '${team_key}'
            order by year;
        """)

CLUTCH_RECORD_SQL = Template("""
            select 
                team.outcome,
                count(*)
            from team_schedules team
            join team_schedules opponent on team.opponent_schedule_week_key=opponent.team_schedule_week_key
            where team.team_key = '${team_key}' and 
                  team.outcome != 'U' and 
                  abs(team.score_for - opponent.score_for) < 10
            group by team.outcome;
        """)

SCHEDULE_SQL = Template("""
    select 
        team.week, 
        teams.team_name, 
        teams.display_name as owner, 
        case when team.outcome = 'U' then null else team.outcome end as outcome,
        case when team.score_for = 0.0 then null else team.score_for end as score_for,
        case when opponent.score_for = 0.0 then null else opponent.score_for end as score_against
    from team_schedules team
    join team_schedules opponent on team.opponent_schedule_week_key=opponent.team_schedule_week_key
    join teams on teams.team_key=opponent.team_key
    where team.team_key='${team_key}' and not team.playoff
    order by week;
""")

async def get_data(owner, year):
    """Get data for owner spotlight page."""
    season_overview_data = await query_data(text(SEASON_OVERVIEW_SQL.substitute(team_key=f"{owner}_{year}")))
    clutch_record_data = await query_data(text(CLUTCH_RECORD_SQL.substitute(team_key=f"{owner}_{year}")))
    schedule_data = await query_data(text(SCHEDULE_SQL.substitute(team_key=f"{owner}_{year}")))

    weeks_played = len([matchup for matchup in schedule_data if matchup["outcome"]])

    season_overview_data = season_overview_data[0]
    season_overview_data["points_for_per_week"] = round(season_overview_data["points_for"] / weeks_played, 2)
    season_overview_data["points_against_per_week"] = round(season_overview_data["points_against"] / weeks_played, 2)

    clutch_record = {d["outcome"]: d["count"] for d in clutch_record_data}
    clutch_record = f"{clutch_record.get('W', 0)}-{clutch_record.get('L', '0')}"

    return season_overview_data, clutch_record, schedule_data


def season_overview_card(title, value):
    """Season Overview card."""
    with ui.card().classes("w-full h-full"):
        ui.label(title).classes("text-weight-bold underline text-xl text-center w-full")
        with ui.row().classes(" h-full w-full items-center"):
            ui.label(value).classes("text-5xl text-center text-bold w-full")


@ui.page("/owners/{owner}/{year}")
async def page(owner: str, year: int):
    """Owner page for each owner."""
    common_header()
    with ui.grid(columns="1fr 1fr").classes("w-full"):
        ui.label(titleize(owner)).classes("text-weight-bold underline text-4xl w-full text-right")
        fantasy_years = await get_fantasy_years()
        with ui.dropdown_button(year).classes("w-1/6"):
            for fantasy_year in fantasy_years:
                ui.item(fantasy_year, on_click=lambda fy=fantasy_year: ui.navigate.to(f"/owners/{owner}/{fy}"))

    season_overview_data, clutch_record, schedule_data = await get_data(owner, year)
    with ui.grid(columns="1fr 1fr 2fr").classes("w-full gap-1"):
        # Owner image
        img_path = MEDIA_PATH_TEMPLATE.substitute(sub_path="owners", file_name=f"{owner}.jpg")
        ui.image(img_path).classes("border p-1")


        # Season Overview
        with ui.card().classes("no-shadow border-[0px] col-span-2"):
            with ui.card_section().classes("w-full").classes("p-0"):
                ui.label("Season Overview").classes("text-weight-bold underline text-3xl text-center")
            with ui.grid(columns="1fr 1fr 1fr 1fr 1fr 1fr").classes("w-full h-full gap-2"):

                season_overview_card("Standing", season_overview_data["standing"])
                season_overview_card("Record", season_overview_data["record"])

                # Points for
                with ui.card().classes("w-full col-span-2"):
                    ui.label("Points for").classes("text-weight-bold underline text-xl text-center w-full")
                    with ui.row().classes("w-full h-full gap-1 items-center justify-center"):
                        ui.label(season_overview_data["points_for"]).classes("text-5xl")
                        ui.label("pts").classes("text-2xl")
                    with ui.row().classes("w-full h-full gap-1 items-center justify-center"):
                        ui.label(season_overview_data["points_for_per_week"]).classes("text-5xl")
                        ui.label("pts/week").classes("text-2xl")

                # Points Against
                with ui.card().classes("w-full col-span-2"):
                    ui.label("Points against").classes("text-weight-bold underline text-xl text-center w-full")
                    with ui.row().classes("w-full h-full gap-1 items-center justify-center"):
                        ui.label(season_overview_data["points_against"]).classes("text-5xl")
                        ui.label("pts").classes("text-2xl")
                    with ui.row().classes("w-full h-full gap-1 items-center justify-center"):
                        ui.label(season_overview_data["points_against_per_week"]).classes("text-5xl")
                        ui.label("pts/week").classes("text-2xl")

                season_overview_card("Streak", season_overview_data["streak"])
                season_overview_card("Clutch Record", clutch_record)
                season_overview_card("Shotguns", "0")
                season_overview_card("Budget", f"${season_overview_data['budget']}")
                season_overview_card("Acquisitions", season_overview_data["acquisitions"])
                season_overview_card("Trades", season_overview_data["trades"])


        # Bio
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("Bio").classes("text-weight-bold underline text-xl text-center")

        # Shotgun Tracker
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("Shotgun Tracker").classes("text-weight-bold underline text-xl text-center")
            data = [
                {"week": "casey_magid", "reason": "1", "link": "1"},
                {"week": "adam_barrett", "reason": "1", "link": "1"},
            ]
            with ui.scroll_area().classes("w-full"):
                await table(data, classes="no-shadow border-[0px] w-full")

        # Schedule
        await table(schedule_data, title="Season Schedule", classes="no-shadow border-[0px] w-full", props="dense")
