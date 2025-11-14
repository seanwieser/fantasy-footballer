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

    # pylint: disable=too-many-locals
    def transform(self, queue):
        """Override parent abstract method to be run by associated s001 extractor."""
        queue.put(f"teams - {self.year}: 0 / {len(self.league.teams)}")
        teams = []
        for team_idx, team in enumerate(self.league.teams):
            team = team.__dict__

            # Convert schedule, scores, outcomes to single object describing a weekly matchup
            new_schedule = []
            schedule_infos = list(zip(team["schedule"], team["scores"], team["outcomes"]))
            for week, schedule_info in enumerate(schedule_infos, start=1):
                opponent, score, outcome = schedule_info

                lineup = []
                self.league.load_roster_week(week=week)
                for team_data in self.league.teams:
                    if team_data.team_id == team["team_id"]:
                        for player in team_data.roster:
                            lineup.append({"playerId": player.playerId, "lineupSlot": player.lineupSlot})

                matchup = {
                    "week": week,
                    "lineup": lineup,
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
