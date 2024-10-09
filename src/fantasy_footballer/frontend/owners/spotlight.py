"""Spotlight page for each owner."""
from datetime import datetime

from backend.io_utils import MEDIA_PATH_TEMPLATE
from frontend.utils import (common_header, get_fantasy_years,
                            image_path_to_owner_name, query_data, table)
from inflection import titleize
from nicegui import ui
from sqlalchemy import text


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

    with ui.grid(columns="1fr 1fr 2fr").classes("w-full gap-1"):
        # Owner image
        img_path = MEDIA_PATH_TEMPLATE.substitute(sub_path="owners", file_name=f"{owner}.jpg")
        ui.image(img_path).classes("border p-1")

        # Season Overview
        with ui.card().classes("no-shadow border-[0px] col-span-2"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("Season Overview").classes("text-weight-bold underline text-xl text-center")
            data = [
                {"week": "casey_magid", "reason": "1", "link": "1"},
                {"week": "adam_barrett", "reason": "1", "link": "1"},
            ]
            with ui.scroll_area().classes("w-full"):
                await table(data, classes="no-shadow border-[0px] w-full virtual-scroll")

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
        sql = text(f"""
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
            where team.team_key='{owner}_{year}' and not team.playoff
            order by week;
        """)
        schedule_data = await query_data(sql)
        await table(schedule_data, title="Season Schedule", classes="no-shadow border-[0px] w-full", props="dense")


