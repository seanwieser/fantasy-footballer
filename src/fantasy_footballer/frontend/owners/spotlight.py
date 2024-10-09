"""Spotlight page for each owner."""
from datetime import datetime

from backend.io_utils import MEDIA_PATH_TEMPLATE
from frontend.utils import common_header, image_path_to_owner_name, query_data, table
from inflection import titleize
from nicegui import ui
from sqlalchemy import text


@ui.page("/owners/{owner}")
async def page(owner):
    """Owner page for each owner."""
    common_header()
    ui.label(titleize(owner)).classes("text-weight-bold underline text-4xl w-full text-center")
    img_path = MEDIA_PATH_TEMPLATE.substitute(sub_path="owners",
                                                  file_name=f"{owner}.jpg")
    with ui.grid(columns="1fr 2fr 1fr").classes("w-full gap-0"):
        # Owner image
        ui.image(img_path).classes("border p-1")

        # Shotgun Tracker
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("Shotgun Tracker").classes("text-weight-bold underline text-xl text-center")
            data = [
                {"week": "casey_magid", "reason": "1", "link": "1"},
                {"week": "adam_barrett", "reason": "1", "link": "1"},
            ]
            with ui.scroll_area().classes("w-full"):
                await table(data, classes="no-shadow border-[0px] w-full virtual-scroll")

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
            where team.team_key='{owner}_{datetime.now().year}'
            order by week;
        """)
        schedule_data = await query_data(sql)
        sorted_schedule_data = sorted(schedule_data, key=lambda x: x["week"])
        await table(sorted_schedule_data, title="Schedule", classes="no-shadow border-[0px] w-full row-span-2", props="dense")

        # Bio
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("Bio").classes("text-weight-bold underline text-xl text-center")

        # History
        with ui.card().classes("no-shadow border-[0px]"):
            with ui.card_section().classes("mx-auto").classes("p-0"):
                ui.label("History").classes("text-weight-bold underline text-xl text-center")
            data = [
                {"year": "casey_magid", "result": "1", "shotguns": "1"},
                {"year": "adam_barrett", "result": "1", "shotguns": "1"},
                {"year": "aditya_sinha", "result": "1", "shotguns": "1"},
                {"year": "casey_magid", "result": "1", "shotguns": "1"},
                {"year": "casey_magid", "result": "1", "shotguns": "1"},
                {"year": "adam_barrett", "result": "1", "shotguns": "1"},
                {"year": "aditya_sinha", "result": "1", "shotguns": "1"},
                {"year": "casey_magid", "result": "1", "shotguns": "1"},

            ]
            await table(data, classes="no-shadow border-[0px] w-full row-span-2")
