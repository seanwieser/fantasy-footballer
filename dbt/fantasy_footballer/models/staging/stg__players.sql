select
    s001_players.player_year_id,
    s001_players.team_year_id,
    s001_players.player_id,
    s001_players.team_id,
    team_current_rosters.owner_id,
    team_current_rosters.owner_year_id,
    team_current_rosters.owner_name,
    s001_players.year,
    s001_players.player_name,
    s001_players.nfl_team,
    team_current_rosters.team_name,
    s001_players.position_slot,
    s001_players.position_slot in ['WR', 'RB', 'TE'] as is_flex, -- noqa
    s001_players.total_points,
    s001_players.avg_points,
    s001_players.position_rank,
    s001_players.eligible_slots,
    s001_players.is_injured,
    s001_players.injury_status,
    s001_players.percent_owned,
    s001_players.percent_started,
    s001_players.projected_avg_points,
    s001_players.projected_total_points,
    s001_players.stats_raw
from {{ ref("base_s001__players") }} as s001_players
left join {{ ref("stg__team_current_rosters") }} as team_current_rosters
    on s001_players.player_year_id = team_current_rosters.player_year_id
