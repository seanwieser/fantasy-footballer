from pydantic import BaseModel
from backend.sources.utils import Transformer
import time

class PlayerSchema(BaseModel):
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
    stats: dict


class PlayersTransformer(Transformer):
    TABLE_NAME = "players"
    TABLE_SCHEMA = PlayerSchema

    def __init__(self, league):
        self.player_map = league.player_map
        self.player_info_func = league.player_info
        super().__init__(table_schema=PlayersTransformer.TABLE_SCHEMA, year=league.year)

    def transform(self):
        players = []
        all_player_ids = [player_id for player_id in self.player_map.keys() if isinstance(player_id, int)]
        for idx, player_id in enumerate(all_player_ids):
            player_obj = self.player_info_func(playerId=player_id)
            if player_obj:
                players.append(self.apply_schema(player_obj))
            if idx % 100 == 0:
                print(f"{idx}/{len(all_player_ids)}")
            time.sleep(0.01)
        print(f"{len(players)} rows transformed")
        return players