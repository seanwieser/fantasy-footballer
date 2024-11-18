from pydantic import BaseModel
from backend.sources.utils import Transformer, DATATYPE_MAP

class TeamSchema(BaseModel):
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
    roster: list
    #
    # @staticmethod
    # def table_definition():
    #     return ", ".join([f"{k} {DATATYPE_MAP[v.annotation]}" for k, v in TeamSchema.model_fields.items()])

class TeamsTransformer(Transformer):
    TABLE_NAME = "teams"
    TABLE_SCHEMA = TeamSchema

    def __init__(self, league):
        self.teams = league.teams
        super().__init__(table_schema=TeamsTransformer.TABLE_SCHEMA, year=league.year)


    def transform(self):
        teams = []
        for team in self.teams:
            team = team.__dict__

            # Convert roster Player objects into playerId's
            team["roster"] =  [player.playerId for player in team["roster"]]

            # Convert schedule and scores to single object
            schedule_scores = list(zip(team["schedule"], team["scores"]))
            team["schedule"] = {opponent.team_id: points_for for opponent, points_for in schedule_scores}

            teams.append(self.apply_schema(team))
        return teams