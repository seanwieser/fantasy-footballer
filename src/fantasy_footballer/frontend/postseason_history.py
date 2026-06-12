"""Module for the Postseason History page."""

from backend.db import DbManager
from frontend.utils import SECTION_COLORS, common_header, get_current_year
from nicegui import ui

COLOR = SECTION_COLORS["Postseason"]

# Placement -> (medal/icon emoji, label) for the season timeline and trophy case.
PLACEMENTS = [
    ("champion", "🥇", "Champion"),
    ("runner_up", "🥈", "Runner-up"),
    ("third", "🥉", "3rd place"),
    ("toilet", "🚽", "Dead last"),
]


def _headshot(owner_id, px=32, ring=None):
    """Circular owner headshot from local media; optional colored ring to mark the winner."""
    classes = "rounded-full shrink-0"
    if ring:
        classes += f" ring-2 ring-offset-2 ring-{ring}-5"
    ui.image(f"resources/media/owners/{owner_id}.jpg") \
        .classes(classes).style(f"width:{px}px;height:{px}px;object-fit:cover")


def _seed_tag(seed):
    """Small muted regular-season seed badge."""
    ui.label(f"#{seed}").classes("text-xs opacity-50 shrink-0")


# Shared hover/cursor affordance for any element that links to an owner-spotlight.
_LINK_CLASSES = "cursor-pointer rounded hover:bg-gray-500/10 transition-colors"


def _link_to_owner(element, owner_id, year):
    """Make a card/row navigate to that owner's season spotlight on click (cross-links the platform)."""
    element.classes(_LINK_CLASSES).on(
        "click", lambda: ui.navigate.to(f"/owner_history/{owner_id}/{year}"))
    return element


# ---- Brackets tab ---------------------------------------------------------------------------

def _participant_row(game, side, is_advancer):
    """One side (`top`/`low`) of a matchup: seed, headshot, name, score — emphasized for the advancer."""
    owner_id = game[f"{side}_seed_owner_id"]
    score = game[f"{side}_seed_score"]
    weight = "font-bold" if is_advancer else "font-normal opacity-70"
    row = _link_to_owner(ui.row().classes("w-full items-center gap-2 no-wrap"), owner_id, game["year"])
    with row:
        _seed_tag(game[f"{side}_seed"])
        _headshot(owner_id, px=26, ring=COLOR if is_advancer else None)
        ui.label(game[f"{side}_seed_owner_name"]).classes(f"{weight} text-sm truncate grow")
        if score is not None:
            ui.label(f"{score:.2f}").classes(f"{weight} text-sm shrink-0")


def _matchup_card(game):
    """A single bracket slot: a two-team game, or a lone bye team auto-advancing."""
    champ = game["is_championship_game"]
    border = f"border-2 border-{COLOR}-5" if champ else "border border-gray-200 dark:border-gray-700"
    with ui.card().classes(f"w-60 gap-1 p-3 rounded-lg {border}"):
        if game["is_bye"]:
            _participant_row(game, "top", is_advancer=True)
            ui.label("BYE").classes("text-xs opacity-40 italic text-center w-full")
            return
        # The advancer is the winner in the championship bracket, but the LOSER in the toilet bowl.
        advancer = game["advancer_owner_id"]
        _participant_row(game, "top", advancer == game["top_seed_owner_id"])
        ui.separator().classes("opacity-30")
        _participant_row(game, "low", advancer == game["low_seed_owner_id"])


def _round_game_label(game):
    """Per-game label, distinguishing the championship from the 3rd-place (consolation) game."""
    if game["is_championship_game"]:
        return "Championship"
    if game["is_third_place_game"]:
        return "Consolation"
    return game["round_label"]


def _round_sort_key(game):
    """Within a round, order the championship first and the consolation (3rd-place) game last."""
    rank = 0 if game["is_championship_game"] else (2 if game["is_third_place_game"] else 1)
    return (rank, game["top_seed"])


def _bracket(title, icon, rows, side_card=None):
    """
    Render one bracket (winners or toilet) as columns of games, one column per round.

    Games within a column carry their own label, so a final column that holds both the Championship
    and the Consolation (3rd-place) game reads clearly. `side_card`, if given, renders to the right of
    the bracket (the podium for the winners bracket, the dead-last finisher for the toilet bowl).
    """
    if not rows:
        return
    rounds = {}
    for row in rows:
        rounds.setdefault(row["round_num"], []).append(row)
    with ui.row().classes("w-full items-center gap-2 mt-4 mb-1"):
        ui.icon(icon, size="1.5rem").classes(f"text-{COLOR}-7")
        ui.label(title).classes(f"text-xl font-bold text-{COLOR}-8")
    with ui.row().classes("w-full items-stretch gap-6 overflow-x-auto pb-2"):
        for round_num in sorted(rounds):
            games = sorted(rounds[round_num], key=_round_sort_key)
            with ui.column().classes("gap-2 justify-center shrink-0"):
                last_label = None
                for game in games:
                    label = _round_game_label(game)
                    if label != last_label:
                        classes = f"text-xs font-semibold uppercase tracking-wide text-{COLOR}-6"
                        if last_label is not None:
                            classes += " mt-2"
                        ui.label(label).classes(classes)
                        last_label = label
                    _matchup_card(game)
        if side_card:
            side_card()


def _luck_column(title, icon, tooltip, rows, year):
    """A titled vertical list of snub / lucky-in owner cards."""
    with ui.column().classes("gap-2 grow min-w-0"):
        with ui.row().classes("items-center gap-2 no-wrap"):
            ui.icon(icon, size="1.3rem").classes(f"text-{COLOR}-7")
            ui.label(title).classes(f"text-lg font-bold text-{COLOR}-8")
            ui.icon("info", size="1rem").classes("opacity-30")
            ui.tooltip(tooltip).classes("text-sm max-w-xs")
        if not rows:
            ui.label("None this season").classes("text-sm opacity-50 italic")
            return
        for row in rows:
            card = _link_to_owner(
                ui.card().classes("w-full gap-2 px-3 py-2 rounded-lg flex-row items-center no-wrap"),
                row["owner_id"], year)
            with card:
                _headshot(row["owner_id"], px=32)
                with ui.column().classes("gap-0 min-w-0"):
                    ui.label(row["owner_name"]).classes("text-sm font-semibold truncate")
                    ui.label(row["detail"]).classes("text-xs opacity-60 truncate")


def _snub_luck_lists(year):
    """Side-by-side Snubs and Lucky-In lists — who got robbed by the bracket vs who snuck in."""
    rows = DbManager.query(f"""
        select owner_id, owner_name, kind, detail
        from main_marts.postseason_snub_luck
        where year = {year}
        order by kind, context_count desc, owner_name
    """, to_dict=True)
    if not rows:
        return
    snubs = [row for row in rows if row["kind"] == "snub"]
    lucky = [row for row in rows if row["kind"] == "lucky_in"]
    ui.separator().classes(f"bg-{COLOR}-3 mt-6")
    with ui.row().classes("w-full gap-8 items-start mt-2"):
        _luck_column("Snubs", "sentiment_very_dissatisfied",
                     "Missed the playoffs despite outscoring at least one team that made it.", snubs, year)
        _luck_column("Lucky-In", "casino",
                     "Made the playoffs despite being outscored by at least one team that missed.", lucky, year)


def _podium_card(timeline, placements, title):
    """Finishers card shown beside a bracket: the winners podium, or the dead-last loser."""
    with ui.card().classes("gap-2 p-4 rounded-xl shadow-sm self-center shrink-0"):
        ui.label(title).classes(f"text-xs font-semibold uppercase tracking-wide text-{COLOR}-7")
        for placement in PLACEMENTS:
            key = placement[0]
            if key in placements and timeline[f"{key}_owner_id"] is not None:
                _finisher_line(placement, timeline)


def _render_brackets(year):
    """Winners + toilet brackets (each with its finishers card), plus the snub / lucky-in lists."""
    rows = DbManager.query(f"""
        select *
        from main_marts.postseason_bracket
        where year = {year}
        order by bracket, round_num, top_seed
    """, to_dict=True)
    timeline_rows = DbManager.query(
        f"select * from main_marts.postseason_timeline where year = {year}", to_dict=True)
    timeline = timeline_rows[0] if timeline_rows else None
    winners = [row for row in rows if row["bracket"] == "winners"]
    toilet = [row for row in rows if row["bracket"] == "toilet_bowl"]
    _bracket("Championship Bracket", "emoji_events", winners,
             side_card=(lambda: _podium_card(timeline, ("champion", "runner_up", "third"), "Podium"))
             if timeline else None)
    _bracket("Toilet Bowl", "delete", toilet,
             side_card=(lambda: _podium_card(timeline, ("toilet",), "Dead Last")) if timeline else None)
    ui.label("In the toilet bowl you advance by LOSING — the final's loser finishes dead last "
             "(and faces horrible humiliation at the hands of their peers).").classes(
        "text-xs opacity-50 italic mt-1")
    _snub_luck_lists(year)


def brackets_tab():
    """Season picker driving a refreshable bracket panel."""
    years = [str(row["year"]) for row in DbManager.query(
        "select distinct year from main_marts.postseason_bracket order by year desc", to_dict=True)]
    default = str(get_current_year())
    if default not in years and years:
        default = years[0]
    season_select = ui.select(years, value=default, label="Season").props("outlined dense").classes("w-40")

    @ui.refreshable
    def panel():
        """Refreshable container for the selected season's brackets."""
        _render_brackets(int(season_select.value))

    season_select.on_value_change(panel.refresh)
    panel()


# ---- Timeline tab ---------------------------------------------------------------------------

def _finisher_line(placement, row):
    """One placement line (champion / runner-up / …) within a season or podium card."""
    key, emoji, label = placement
    owner_id = row[f"{key}_owner_id"]
    line = _link_to_owner(ui.row().classes("w-full items-center gap-2 no-wrap"), owner_id, row["year"])
    with line:
        ui.label(emoji).classes("text-lg w-6 text-center shrink-0")
        _headshot(owner_id, px=30)
        with ui.column().classes("gap-0 min-w-0 grow"):
            ui.label(row[f"{key}_owner_name"]).classes("text-sm font-semibold truncate")
            ui.label(label).classes("text-xs opacity-50")
        _seed_tag(row[f"{key}_seed"])


def _season_card(row):
    """A season's four headline finishers, champion banner on top."""
    with ui.card().classes("w-72 gap-2 p-4 rounded-xl shadow-sm"):
        ui.label(str(row["year"])).classes(f"text-2xl font-bold text-{COLOR}-8 w-full text-center")
        ui.separator().classes(f"bg-{COLOR}-3")
        for placement in PLACEMENTS:
            if row[f"{placement[0]}_owner_id"] is not None:
                _finisher_line(placement, row)


def timeline_tab():
    """Newest-first grid of season finisher cards."""
    rows = DbManager.query("select * from main_marts.postseason_timeline order by year desc", to_dict=True)
    with ui.row().classes("w-full gap-4 justify-center"):
        for row in rows:
            _season_card(row)


# ---- Trophy case tab ------------------------------------------------------------------------

def _trophy_count(emoji, count, label):
    """A medal tally chip (hidden when zero)."""
    if not count:
        return
    with ui.row().classes("items-center gap-1 no-wrap"):
        ui.label(emoji).classes("text-base")
        ui.label(f"×{count}").classes("text-sm font-semibold")
        ui.tooltip(label).classes("text-xs")


def _trophy_card(owner):
    """One owner's career hardware + playoff / toilet records, as a slim single row."""
    card = _link_to_owner(
        ui.card().classes("w-full gap-3 px-3 py-2 rounded-lg shadow-sm flex-row items-center no-wrap"),
        owner["owner_id"], owner["last_year"])
    with card:
        _headshot(owner["owner_id"], px=34, ring=COLOR if owner["championships"] else None)
        with ui.column().classes("gap-0 min-w-0 grow"):
            ui.label(owner["owner_name"]).classes("text-sm font-bold truncate")
            record = f"{owner['playoff_wins']}-{owner['playoff_losses']} Playoffs"
            if owner["toilet_bowl_wins"] + owner["toilet_bowl_losses"] > 0:
                record += f" · {owner['toilet_bowl_wins']}-{owner['toilet_bowl_losses']} Toilet Bowl"
            ui.label(record).classes("text-xs opacity-60 truncate")
        with ui.row().classes("items-center gap-3 shrink-0"):
            _trophy_count("🥇", owner["championships"], "Championships")
            _trophy_count("🥈", owner["runner_ups"], "Runner-ups")
            _trophy_count("🥉", owner["third_places"], "3rd-place finishes")
            _trophy_count("🚽", owner["last_place_finishes"], "Dead-last finishes")


def trophy_case_tab():
    """Per-owner career trophy case, most-decorated first."""
    owners = DbManager.query("select * from main_marts.postseason_trophy_case", to_dict=True)
    with ui.column().classes("w-full gap-2 max-w-2xl mx-auto"):
        for owner in owners:
            _trophy_card(owner)


@ui.page("/postseason_history")
def page():
    """Postseason History page."""
    common_header()
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-7xl w-full gap-2"):
            ui.label("Postseason History").classes("text-4xl font-semibold w-full text-center")
            ui.label("Champions, toilet bowls, and every bracket the league has played").classes(
                "text-base opacity-60 w-full text-center mb-2")
            with ui.tabs().classes("w-full") as tabs:
                brackets = ui.tab("Brackets", icon="account_tree")
                timeline = ui.tab("Timeline", icon="calendar_month")
                trophies = ui.tab("Trophy Case", icon="emoji_events")
            with ui.tab_panels(tabs, value=brackets).classes("w-full"):
                with ui.tab_panel(brackets):
                    brackets_tab()
                with ui.tab_panel(timeline):
                    timeline_tab()
                with ui.tab_panel(trophies):
                    trophy_case_tab()
