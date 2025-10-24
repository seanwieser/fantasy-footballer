"""Module containing pydantic model and transformer for s001 players source table."""

from backend.utils import Transformer
from pydantic import BaseModel


class PlayerSchema(BaseModel):
    """Pydantic model to define schema for players source table."""

    playerId: int
    name: str
    posRank: int | list
    lineupSlot: str
    eligibleSlots: list[str]
    acquisitionType: str | list
    proTeam: str
    onTeamId: int
    position: str
    injuryStatus: str | list
    injured: bool
    total_points: float
    avg_points: float
    projected_total_points: float
    projected_avg_points: float
    percent_owned: float
    percent_started: float
    stats: list


class PlayersTransformer(Transformer):
    """Transformer class for s001 players source data."""

    TABLE_NAME = "players"
    TABLE_SCHEMA = PlayerSchema

    def __init__(self, league):
        self.player_map = league.player_map
        self.player_info_func = league.player_info
        super().__init__(table_schema=PlayersTransformer.TABLE_SCHEMA, year=league.year)

    def transform(self, queue):
        """Override parent abstract method to be run by associated s001 extractor."""
        players = []
        all_player_ids = [player_id for player_id in self.player_map.keys() if isinstance(player_id, int)]
        all_player_ids_count = len(all_player_ids)
        queue.put(f"0 / {all_player_ids_count}")
        for idx, player_id in enumerate(all_player_ids):
            player_obj = self.player_info_func(playerId=player_id)
            if not player_obj:
                continue

            player_dict = self.convert_to_dict(player_obj)

            # Reformat 'stats' as a list of dicts
            new_stats = []
            for week, stat in player_dict["stats"].items():
                breakdown = stat.pop("breakdown")
                new_stat = {"week": week} | stat | breakdown
                new_stats.append(new_stat)
            player_dict["stats"] = new_stats

            # Apply PlayerSchema
            players.append(self.apply_schema(player_dict))

            # Update queue for frontend progress bar
            queue.put(f"{idx + 1} / {all_player_ids_count}")

        return players
