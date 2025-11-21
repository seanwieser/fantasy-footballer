select
    owner_team_year_map.year,
    owner_team_year_map.owner_name,
    owner_team_year_map.team_name,
    draftpicks.player_name,
    draftpicks.round_num,
    draftpicks.round_pick,
    draftpicks.bid_amount,
    draftpicks.keeper_status,
    draftpicks.nominating_team_id,
    draftpicks.is_auction
from {{ ref("base_s001__draftpicks") }} draftpicks
inner join {{ ref("int__owner_team_year_map") }} owner_team_year_map
on draftpicks.team_year_id = owner_team_year_map.team_year_id