select
    year,
    player_name,
    position_slot as position,
    position_rank,
    nfl_team,
    round(total_points, 2) as total_points,
    round(total_points / num_weeks, 2) as avg_points
from {{ ref("int__player_season_stats") }}
order by total_points desc
