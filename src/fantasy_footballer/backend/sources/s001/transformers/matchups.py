"""Module containing pydantic model and transformer for s001 matchups source table."""

from backend.utils import NUM_NFL_WEEKS, Transformer
from pydantic import BaseModel


class MatchupSchema(BaseModel):
    """Pydantic model to define schema for matchups source table."""

    matchup_week: int
    home_team: int
    home_score: float
    home_projected: float
    away_team: None | int
    away_score: float
    away_projected: float
    home_lineup: list
    away_lineup: list
    is_playoff: bool
    matchup_type: str


class MatchupTransformer(Transformer):
    """Transformer class for s001 matchups source data."""

    TABLE_NAME = "matchups"
    TABLE_SCHEMA = MatchupSchema

    def __init__(self, league):
        self.box_score_func = league.box_scores
        super().__init__(table_schema=MatchupTransformer.TABLE_SCHEMA, year=league.year)


    def transform(self, queue):
        """Override parent abstract method to be run by associated s001 extractor."""
        queue.put(f"matchups - {self.year}: 0 / {NUM_NFL_WEEKS}")
        matchups = []
        for matchup_week in range(1, NUM_NFL_WEEKS + 1):
            for matchup in self.box_score_func(matchup_week):
                matchup =  matchup.__dict__

                matchup["matchup_week"] = matchup_week

                # Playoff bye weeks do not have an away team
                if isinstance(matchup["away_team"], int):
                    matchup["away_team"] = None
                    matchup["away_lineup"] = []
                else:
                    matchup["away_team"] =  matchup["away_team"].team_id
                    matchup["away_lineup"] = [away_player.playerId for away_player in  matchup["away_lineup"]]

                matchup["home_team"] =  matchup["home_team"].team_id
                matchup["home_lineup"] = [home_player.playerId for home_player in  matchup["home_lineup"]]

                matchups.append(self.apply_schema(matchup))

            # Update queue for frontend progress bar
            queue.put(f"matchups - {self.year}: {matchup_week} / {NUM_NFL_WEEKS}")

        return matchups
