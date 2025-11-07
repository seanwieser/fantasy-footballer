"""Module containing pydantic model and transformer for s001 matchups source table."""

from backend.utils import Transformer
from pydantic import BaseModel


class SettingsSchema(BaseModel):
    """Pydantic model to define schema for settings source table."""

    reg_season_count: int
    matchup_periods: dict
    veto_votes_required: int
    team_count: int
    playoff_team_count: int
    keeper_count: int
    trade_deadline: int
    division_map: dict
    name: str
    tie_rule: str
    playoff_tie_rule: str
    playoff_matchup_period_length: int
    playoff_seed_tie_rule: str
    scoring_type: str
    faab: bool
    acquisition_budget: None | int
    scoring_format: list[dict]
    position_slot_counts: dict


class SettingsTransformer(Transformer):
    """Transformer class for s001 settings source data."""

    TABLE_NAME = "settings"
    TABLE_SCHEMA = SettingsSchema

    def __init__(self, league):
        self.settings = league.settings
        super().__init__(table_schema=SettingsTransformer.TABLE_SCHEMA, year=league.year)


    def transform(self, queue):
        """Override parent abstract method to be run by associated s001 extractor."""
        settings = self.apply_schema(self.settings.__dict__)
        queue.put(f"settings: {self.year}")
        return settings
