select
    owner_map.owner_id,
    lineup.year,
    lineup.matchup_week,
    lineup.week,
    lineup.is_playoff,
    lineup.player_week_id,
    lineup.player_name,
    lineup.position,
    round(lineup.points, 2) as points,
    lineup.is_started,
    lineup.is_optimal,
    lineup.actual_slot,
    lineup.optimal_slot
from {{ ref("int__optimal_lineup_players") }} as lineup
inner join {{ ref("int__owner_team_year_map") }} as owner_map
    on lineup.team_year_id = owner_map.team_year_id
