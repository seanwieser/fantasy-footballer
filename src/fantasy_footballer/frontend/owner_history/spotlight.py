"""Spotlight page for each owner."""
from backend.db import DbManager
from frontend.utils import (SECTION_COLORS, common_header, format_field_name,
                            get_years_by_owner_id, medal,
                            owner_id_to_owner_name, table)
from nicegui import ui

# Week-grain schedule events -> (material icon, standardized highlight section, tooltip). The
# chip color comes from SECTION_COLORS[section], so the schedule shares the League Highlights
# palette: Scoring=blue, Matchups=orange, Shotgun=green, Clutch=red. With no legend, each tooltip
# carries the full definition; every flag is the week-level occurrence of a season highlight.
SCHEDULE_FLAGS = {
    "is_best_week": ("trending_up", "Scoring", "Best-week title — league's single highest score this season"),
    "is_worst_week": ("trending_down", "Scoring", "Worst-week title — league's single lowest score this season"),
    "is_lucky_win": ("sentiment_very_satisfied", "Matchups", "Lucky win — won while scoring below the league median"),
    "is_unlucky_loss": ("heart_broken", "Matchups", "Unlucky loss — lost while scoring above the league median"),
    "is_shotgun": ("sports_bar", "Shotgun", "Shotgun — scored under 100 or the week's league low"),
    "is_clutch_win": ("bolt", "Clutch", "Clutch win — won a game decided by under 10 points"),
    "is_clutch_loss": ("flash_off", "Clutch", "Clutch loss — lost a game decided by under 10 points"),
    "is_tightest_game": ("compress", "Matchups", "Tightest game — season's smallest margin of victory"),
    "is_biggest_blowout": ("open_in_full", "Matchups", "Biggest blowout — season's largest margin of victory"),
}


def season_overview_card(title, value, tooltip_text=None):
    """Season Overview card."""
    with ui.card().classes("w-full h-full") as card:
        if tooltip_text:
            card.tooltip(tooltip_text)
        ui.label(title).classes("text-weight-bold underline text-xl text-center w-full")
        with ui.row().classes(" h-full w-full items-center"):
            ui.label(value).classes("text-5xl text-center text-bold w-full")


def highlights_card(owner_id, year):
    """League-highlight podium finishes (gold/silver/bronze) this owner earned that season."""
    rows = DbManager.query(
        f"""
        select section, metric_label, display_value, detail, rank
        from main_marts.season_highlights
        where owner_id={owner_id} and year={str(year)}
        order by display_order, rank
        """,
        to_dict=True,
    )
    with ui.card().classes("no-shadow border-[0px] col-span-2 w-full h-full"):
        ui.label("Highlights").classes("text-weight-bold underline text-xl text-center w-full")
        if not rows:
            ui.label("No podium finishes this season").classes("mx-auto text-gray-500")
            return
        with ui.column().classes("w-full gap-2"):
            for row in rows:
                color = SECTION_COLORS.get(row["section"], "grey")
                with ui.row().classes("w-full items-center gap-2 no-wrap"):
                    ui.label(medal(row["rank"])).classes("text-base shrink-0")
                    with ui.column().classes("gap-0 min-w-0 grow"):
                        ui.label(row["metric_label"]).classes("text-sm font-medium truncate")
                        if row["detail"]:
                            ui.label(row["detail"]).classes("text-xs opacity-60 truncate")
                    ui.label(row["display_value"]).classes(f"text-sm font-semibold text-{color}-7 ml-auto shrink-0")


def _highlights_slot():
    """q-table body-cell slot: a section-colored chip (icon + tooltip) per active week flag."""
    chips = ""
    for flag, (icon, section, label) in SCHEDULE_FLAGS.items():
        color = SECTION_COLORS[section]
        field = format_field_name(flag)  # row key after the table helper formats column names
        chips += (
            f'<span v-if="props.row[\'{field}\']" '
            f'class="inline-flex items-center justify-center rounded-full bg-{color}-1 q-mr-xs" '
            f'style="width:20px;height:20px">'
            f'<q-icon name="{icon}" color="{color}-8" size="14px" />'
            f'<q-tooltip>{label}</q-tooltip></span>'
        )
    return {"name": "body-cell-Highlights", "template": f'<q-td :props="props">{chips}</q-td>'}


def season_schedule_table(owner_id, year, on_week_click=None):
    """
    Dense weekly schedule; a Highlights column of section-colored chips replaces cell tints.

    When `on_week_click` is given, clicking a row calls it with that week (jumps the Roster tab).
    """
    schedule_sql = f"""
        select
            week as "Week",
            opponent_team_name as "Team_Name",
            opponent_owner_name as "Owner",
            outcome as "Outcome",
            if(outcome = '', '', printf('%.2f', score_for)) as "Points_For",
            if(outcome = '', '', printf('%.2f', score_against)) as "Points_Against",
            '' as "Highlights",
            {', '.join(SCHEDULE_FLAGS)}
        from main_marts.season_schedule
        where owner_id={owner_id} and year={str(year)}
        order by week
    """
    season_data_df = DbManager.query(schedule_sql)

    schedule_table = table(season_data_df,
                           classes="no-shadow border-[0px] w-full" + (" cursor-pointer" if on_week_click else ""),
                           props="dense",
                           not_sortable=["Team Name", "Owner", "Outcome", "Highlights"],
                           hidden_fields=list(SCHEDULE_FLAGS),
                           slots=[_highlights_slot()])
    if on_week_click is not None:
        schedule_table.on("rowClick", lambda event: on_week_click(int(event.args[1]["Week"])))


# Starting-lineup slot display order for the weekly Roster view.
LINEUP_SLOT_ORDER = {"QB": 0, "RB": 1, "WR": 2, "TE": 3, "FLEX": 4, "K": 5, "D/ST": 6}


def _lineup_column(title, rows, slot_field, differs, accent):
    """
    Render one lineup (your actual or the optimal) as slot · player · points rows.

    Rows that differ between actual and optimal are marked with a left accent border and bright
    accent text (readable on the dark page; a light fill would wash the default light text out).
    """
    with ui.column().classes("flex-1 gap-1 min-w-0"):
        ui.label(title).classes("text-weight-bold text-center w-full underline")
        for row in sorted(rows, key=lambda r: LINEUP_SLOT_ORDER.get(r[slot_field], 9)):
            changed = differs(row)
            row_classes = "w-full items-center gap-2 no-wrap rounded px-1"
            if changed:
                row_classes += f" border-l-4 border-{accent}-5"
            with ui.row().classes(row_classes):
                slot_classes = "text-xs w-12 shrink-0 " + (f"text-{accent}-4" if changed else "opacity-60")
                ui.label(row[slot_field]).classes(slot_classes)
                name_classes = "text-sm grow truncate" + (f" text-{accent}-4 font-medium" if changed else "")
                ui.label(row["player_name"]).classes(name_classes)
                points_classes = "text-sm font-semibold shrink-0" + (f" text-{accent}-4" if changed else "")
                ui.label(f"{row['points']:.1f}").classes(points_classes)


def _season_roster(owner_id, year):
    """The 'All' view: every player the owner rostered that season and how much they were used."""
    roster_df = DbManager.query(f"""
        select
            player_name                                as "Player",
            position                                   as "Pos",
            weeks_held                                 as "Weeks",
            weeks_started                              as "Started",
            printf('%.1f', points_held)                as "Rostered_Pts",
            printf('%.1f', points_started)             as "Started_Pts",
            if(roster_utilization is null, '—',
               round(roster_utilization * 100, 0)::int::varchar || '%') as "Util"
        from main_marts.owner_roster_production
        where owner_id={owner_id} and year={str(year)}
        order by points_started desc, points_held desc
    """)
    if roster_df.empty:
        ui.label("No roster data this season").classes("mx-auto text-gray-500 p-4")
        return
    table(roster_df,
          classes="no-shadow border-[0px] w-full",
          props="dense",
          not_sortable=["Player", "Pos"])


@ui.refreshable
def weekly_roster_view(owner_id, year, week):
    """Your actual starting lineup vs the optimal legal lineup for the week (or All = season roster)."""
    if week == "All":
        _season_roster(owner_id, year)
        return

    rows = DbManager.query(f"""
        select player_name, points, is_started, is_optimal, actual_slot, optimal_slot, is_playoff
        from main_marts.owner_weekly_lineup
        where owner_id={owner_id} and year={str(year)} and week={week} and (is_started or is_optimal)
    """, to_dict=True)

    if not rows:
        ui.label("No lineup set this week").classes("mx-auto text-gray-500 p-4")
        return

    actual = [row for row in rows if row["is_started"]]
    optimal = [row for row in rows if row["is_optimal"]]
    points_left = sum(row["points"] for row in optimal) - sum(row["points"] for row in actual)

    with ui.row().classes("w-full items-center justify-between px-1"):
        week_label = f"Week {week}" + (" · Postseason" if rows[0]["is_playoff"] else "")
        ui.label(week_label).classes("text-lg text-weight-bold")
        left_color = "amber" if points_left > 0.05 else "green"
        ui.label(f"{points_left:.1f} pts left on the bench").classes(f"text-{left_color}-8 font-medium")
    with ui.row().classes("w-full gap-6 no-wrap"):
        _lineup_column("Your lineup", actual, "actual_slot", lambda r: not r["is_optimal"], "red")
        _lineup_column("Optimal lineup", optimal, "optimal_slot", lambda r: not r["is_started"], "green")


def postseason_schedule_table(owner_id, year, on_week_click=None):
    """
    That owner-season's postseason games, or an empty state if they missed the bracket.

    When `on_week_click` is given, clicking a row jumps the Roster tab to that postseason week.
    """
    postseason_df = DbManager.query(f"""
        select
            round_label         as "Round",
            opponent_team_name  as "Team_Name",
            opponent_owner_name as "Opponent",
            outcome             as "Outcome",
            if(score_for is null, '', printf('%.2f', score_for))         as "Points_For",
            if(score_against is null, '', printf('%.2f', score_against)) as "Points_Against",
            week                as "Week"
        from main_marts.postseason_schedule
        where owner_id={owner_id} and year={str(year)}
        order by round_num
    """)

    if postseason_df.empty:
        ui.label("Missed the postseason this year").classes("mx-auto text-gray-500 p-4")
        return

    postseason_table = table(postseason_df,
                             classes="no-shadow border-[0px] w-full" + (" cursor-pointer" if on_week_click else ""),
                             props="dense",
                             not_sortable=["Round", "Team Name", "Opponent", "Outcome"],
                             hidden_fields=["Week"])
    if on_week_click is not None:
        postseason_table.on("rowClick", lambda event: on_week_click(int(event.args[1]["Week"])))


@ui.page("/owner_history/{owner_id}/{year}")
def page(owner_id: str, year: int):  # pylint:disable=too-many-statements,too-many-locals
    """Owner page for each owner/year combination."""
    common_header()
    with ui.grid(columns="1fr 1fr").classes("w-full"):
        owner_name = owner_id_to_owner_name(owner_id)
        ui.label(owner_name).classes("text-weight-bold underline text-4xl w-full text-right")
        fantasy_years = get_years_by_owner_id(owner_id)
        with ui.dropdown_button(str(year)).classes("w-1/6"):
            for fantasy_year in fantasy_years:
                ui.item(fantasy_year,
                        on_click=lambda fy=fantasy_year: ui.navigate.to(f"/owner_history/{owner_id}/{fy}"))

    with ui.grid(columns="1fr 1fr 2fr").classes("w-full gap-1"):
        # Owner image
        img_path = f"resources/media/owners/{owner_id}.jpg"
        ui.image(img_path).classes("border p-1")

        # Regular Season Overview
        season_overview_sql = f"select * from main_marts.season_overview where owner_id={owner_id} and year={str(year)}"
        season_overview_data = DbManager.query(season_overview_sql, to_dict=True)[0]
        with ui.card().classes("no-shadow border-[0px] col-span-2"):
            with ui.card_section().classes("w-full").classes("p-0"):
                ui.label("Regular Season Overview").classes("text-weight-bold underline text-3xl text-center")
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

                season_overview_card("Current Streak", season_overview_data["streak"])
                season_overview_card("Clutch Record",
                                     season_overview_data["clutch_record"],
                                     tooltip_text="Matchups within 10 points")
                season_overview_card("Shotguns",
                                     season_overview_data["shotguns"],
                                     tooltip_text="Under 100 Points For or lowest of week")
                season_overview_card("Budget", f"${season_overview_data['budget']}")
                season_overview_card("Acquisitions", season_overview_data["acquisitions"])
                season_overview_card("Trades", season_overview_data["trades"])

        # Highlights
        with ui.column().classes("w-full gap-4"):
            highlights_card(owner_id, year)

        # Schedule / Roster / Postseason tabs
        with ui.card().classes("no-shadow border-[0px] col-span-2 w-full"):
            with ui.tabs().classes("w-full") as schedule_tabs:
                regular_tab = ui.tab("Regular Season")
                roster_tab = ui.tab("Roster")
                postseason_tab = ui.tab("Postseason")

            with ui.tab_panels(schedule_tabs, value=regular_tab).classes("w-full").style("min-height: 620px"):
                # Roster panel is built first so the schedule's row-click can target its week select.
                with ui.tab_panel(roster_tab):
                    week_rows = DbManager.query(
                        f"select distinct week, is_playoff from main_marts.owner_weekly_lineup "
                        f"where owner_id={owner_id} and year={str(year)} order by week", to_dict=True)
                    # Dict options keep numeric week values while labeling postseason weeks distinctly.
                    week_options = {"All": "All"}
                    for row in week_rows:
                        week_options[row["week"]] = f"Week {row['week']}" + (" · PO" if row["is_playoff"] else "")
                    week_select = ui.select(week_options, value="All", label="Week") \
                        .props("outlined dense").classes("w-40")
                    week_select.on_value_change(
                        lambda: weekly_roster_view.refresh(owner_id, year, week_select.value))
                    weekly_roster_view(owner_id, year, "All")

                def goto_week(week):
                    week_select.set_value(week)
                    schedule_tabs.set_value(roster_tab)

                with ui.tab_panel(regular_tab):
                    season_schedule_table(owner_id, year, on_week_click=goto_week)
                with ui.tab_panel(postseason_tab):
                    postseason_schedule_table(owner_id, year, on_week_click=goto_week)
