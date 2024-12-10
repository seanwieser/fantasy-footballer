"""Module containing pydantic model and transformer for s001 teams source table."""

from backend.sources.utils import Transformer
from pydantic import BaseModel


class TeamSchema(BaseModel):
    """Pydantic model to define schema for teams source table."""

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
    roster: list
    schedule: list


class TeamsTransformer(Transformer):
    """Transformer class for s001 teams source data."""

    TABLE_NAME = "teams"
    TABLE_SCHEMA = TeamSchema

    def __init__(self, league):
        self.teams = league.teams
        super().__init__(table_schema=TeamsTransformer.TABLE_SCHEMA, year=league.year)


    def transform(self, queue):
        """Override parent abstract method to be run by associated s001 extractor."""
        teams = []
        for team_idx, team in enumerate(self.teams):
            team = team.__dict__

            # Convert roster Player objects into playerId's
            team["roster"] =  [player.playerId for player in team["roster"]]

            # Convert schedule, scores, outcomes to single object describing a weekly matchup
            new_schedule = []
            schedule_infos = list(zip(team["schedule"], team["scores"], team["outcomes"]))
            for schedule_idx, schedule_info in enumerate(schedule_infos):
                opponent, score, outcome = schedule_info
                matchup = {
                    "week": schedule_idx + 1,
                    "score_for": score,
                    "outcome": outcome,
                    "opponent": self.convert_to_dict(opponent)["team_name"]
                }
                new_schedule.append(matchup)
            team["schedule"] = new_schedule

            # Apply TableSchema
            teams.append(self.apply_schema(team))

            # Update queue for frontend progress bar
            queue.put_nowait((team_idx + 1) / len(self.teams))

        return teams
