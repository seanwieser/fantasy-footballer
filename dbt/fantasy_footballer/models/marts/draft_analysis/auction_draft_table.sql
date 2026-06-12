select
    owner_team_year_map.year,
    owner_team_year_map.owner_name as owner,
    owner_team_year_map.owner_id,
    owner_team_year_map.team_name as team,
    nominating_owner_team_year_map.owner_name as nominating_owner,
    draftpicks.player_name as player,
    players.position_slot as position,
    draftpicks.round_num as round,
    draftpicks.round_pick,
    draftpicks.bid_amount,
    draftpicks.keeper_status::varchar as keeper
from {{ ref("base_s001__draftpicks") }} as draftpicks
inner join {{ ref("int__owner_team_year_map") }} as owner_team_year_map
    on draftpicks.team_year_id = owner_team_year_map.team_year_id
inner join {{ ref("int__owner_team_year_map") }} as nominating_owner_team_year_map
    on draftpicks.nominating_team_year_id = nominating_owner_team_year_map.team_year_id
left join {{ ref("base_s001__players") }} as players
    on draftpicks.player_year_id = players.player_year_id
where draftpicks.is_auction
