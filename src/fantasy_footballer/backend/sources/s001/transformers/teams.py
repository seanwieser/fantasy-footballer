"""Module containing pydantic model and transformer for s001 teams source table."""

from backend.utils import Transformer
from pydantic import BaseModel


class TeamSchema(BaseModel):
    """Pydantic model to define schema for teams source table."""

    team_id: int
    team_abbrev: str
    team_name: str
    division_id: int
    division_name: str
    wins: int
    losses: int
    ties: int
    points_for: float
    points_against: float
    acquisitions: int
    acquisition_budget_spent: int
    drops: int
    trades: int
    playoff_pct: float
    draft_projected_rank: int
    streak_length: int
    streak_type: str
    standing: int
    final_standing: int
    owners: list
    schedule: list


class TeamsTransformer(Transformer):
    """Transformer class for s001 teams source data."""

    TABLE_NAME = "teams"
    TABLE_SCHEMA = TeamSchema

    def __init__(self, league):
        self.league = league
        super().__init__(table_schema=TeamsTransformer.TABLE_SCHEMA, year=league.year)

    def _rosters_by_nfl_week(self):
        """
        Map every NFL scoring week -> {team_id: [{playerId, lineupSlot}]}.

        A matchup period can span more than one NFL week (the 2018-2019 two-week playoff matchups), and
        `load_roster_week` takes the *NFL scoring period* — so rosters are loaded per NFL week (cached
        once, since each call refreshes every team) and later grouped back under their matchup period.
        """
        nfl_weeks = sorted({
            week for weeks in self.league.settings.matchup_periods.values() if weeks for week in weeks
        })
        rosters = {}
        for nfl_week in nfl_weeks:
            self.league.load_roster_week(week=nfl_week)
            rosters[nfl_week] = {
                team.team_id: [
                    {"playerId": player.playerId, "lineupSlot": player.lineupSlot}
                    for player in team.roster
                ]
                for team in self.league.teams
            }
        return rosters

    # pylint: disable=too-many-locals
    def transform(self, queue):
        """Override parent abstract method to be run by associated s001 extractor."""
        queue.put(f"teams - {self.year}: 0 / {len(self.league.teams)}")
        matchup_periods = self.league.settings.matchup_periods
        rosters_by_nfl_week = self._rosters_by_nfl_week()

        teams = []
        for team_idx, team in enumerate(self.league.teams):
            team = team.__dict__

            # Convert schedule, scores, outcomes to single object describing each matchup period; the
            # matchup score/outcome are per matchup period while lineups are captured per NFL week.
            new_schedule = []
            schedule_infos = list(zip(team["schedule"], team["scores"], team["outcomes"]))
            for matchup_week, schedule_info in enumerate(schedule_infos, start=1):
                opponent, score, outcome = schedule_info
                nfl_weeks = matchup_periods.get(str(matchup_week)) or [matchup_week]
                lineups = [
                    {"week": nfl_week, "players": rosters_by_nfl_week[nfl_week][team["team_id"]]}
                    for nfl_week in nfl_weeks
                    if nfl_week in rosters_by_nfl_week
                ]

                matchup = {
                    "week": matchup_week,
                    "lineups": lineups,
                    "score_for": score,
                    "outcome": outcome,
                    "opponent_team_id": self.convert_to_dict(opponent)["team_id"]
                }
                new_schedule.append(matchup)
            team["schedule"] = new_schedule

            # Apply TableSchema
            teams.append(self.apply_schema(team))

            # Update queue for frontend progress bar
            queue.put(f"teams - {self.year}: {team_idx + 1} / {len(self.league.teams)}")

        return teams
