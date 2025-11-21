"""Module containing pydantic model and transformer for s001 draftpicks source table."""

from backend.utils import Transformer
from pydantic import BaseModel


class DraftPickSchema(BaseModel):
    """Pydantic model to define schema for draftpicks source table."""

    team_id: int
    playerId: int
    playerName: str
    round_num: int
    round_pick: int
    bid_amount: int
    keeper_status: bool
    nominating_team_id: None | int


class DraftPickTransformer(Transformer):
    """Transformer class for s001 draftpicks source data."""

    TABLE_NAME = "draftpicks"
    TABLE_SCHEMA = DraftPickSchema

    def __init__(self, league):
        self.draft = league.draft
        super().__init__(table_schema=DraftPickTransformer.TABLE_SCHEMA, year=league.year)


    def transform(self, queue):
        """Override parent abstract method to be run by associated s001 extractor."""
        draft_picks = []
        all_draft_picks_count = len(self.draft)
        queue.put(f"draftpicks - {self.year}: 0 / {all_draft_picks_count}")
        for idx, pick in enumerate(self.draft, start = 1):
            pick = pick.__dict__
            pick["team_id"] = pick["team"].team_id

            # Nominating team is None if snake draft
            if pick["nominatingTeam"]:
                pick["nominating_team_id"] = pick["nominatingTeam"].team_id
            else:
                pick["nominating_team_id"] = None

            draft_picks.append(self.apply_schema(pick))
            queue.put(f"draftpicks - {self.year}: {idx} / {all_draft_picks_count}")

        return draft_picks
