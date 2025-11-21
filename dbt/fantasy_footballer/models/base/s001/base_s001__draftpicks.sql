select
    team_id::varchar || '_' || year::varchar as team_year_id,
    playerid::varchar || '_' || year::varchar as player_year_id,

    team_id::int as team_id,
    playerid::int as player_id,
    year::int as year,

    playername::varchar as player_name,
    round_num::int as round_num,
    round_pick::int as round_pick,
    bid_amount::int as bid_amount,
    keeper_status::bool as keeper_status,
    nominating_team_id::int as nominating_team_id,
    nominating_team_id is not null as is_auction,
    meta__source_path::varchar as meta__source_path,
    meta__date_effective::date as meta__date_effective,
    meta__date_pulled::date as meta__date_pulled
from {{ source("s001", "draftpicks") }}
