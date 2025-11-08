"""Module containing pydantic model and transformer for s001 matchups source table."""

from backend.utils import NUM_NFL_WEEKS, Transformer
from pydantic import BaseModel


class MatchupSchema(BaseModel):
    """Pydantic model to define schema for matchups source table."""

    matchup_week: int
    home_team: int
    home_score: float
    home_projected: None | float
    away_team: None | int
    away_score: float
    away_projected: None | float
    home_lineup: None | list
    away_lineup: None | list
    is_playoff: bool
    matchup_type: str


class MatchupTransformer(Transformer):
    """Transformer class for s001 matchups source data."""

    TABLE_NAME = "matchups"
    TABLE_SCHEMA = MatchupSchema

    def __init__(self, league):
        self.box_score_func = league.box_scores
        self.scoreboard_func = league.scoreboard
        super().__init__(table_schema=MatchupTransformer.TABLE_SCHEMA, year=league.year)


    def transform(self, queue):
        """Override parent abstract method to be run by associated s001 extractor."""
        queue.put(f"matchups - {self.year}: 0 / {NUM_NFL_WEEKS}")

        # box_scores does not work before 2019
        matchup_func = self.box_score_func
        if self.year == 2018:
            matchup_func = self.scoreboard_func

        matchups = []
        for matchup_week in range(1, NUM_NFL_WEEKS + 1):
            for matchup in matchup_func(matchup_week):
                matchup =  matchup.__dict__

                matchup["matchup_week"] = matchup_week
                matchup["home_team"] = matchup["home_team"].team_id
                if self.year > 2018:
                    matchup["home_lineup"] = [home_player.playerId for home_player in matchup["home_lineup"]]

                if not isinstance(matchup["away_team"], int) and self.year > 2018:
                    matchup["away_team"] = matchup["away_team"].team_id
                    matchup["away_lineup"] = [away_player.playerId for away_player in matchup["away_lineup"]]
                elif not isinstance(matchup["away_team"], int):
                    matchup["away_team"] = matchup["away_team"].team_id
                    matchup["away_lineup"] = []
                else:
                    matchup["away_team"] = None
                    matchup["away_lineup"] = []

                matchups.append(self.apply_schema(matchup))

            # Update queue for frontend progress bar
            queue.put(f"matchups - {self.year}: {matchup_week} / {NUM_NFL_WEEKS}")

        return matchups
