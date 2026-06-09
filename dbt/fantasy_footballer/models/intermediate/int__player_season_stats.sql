select
    year,
    player_year_id,
    player_name,
    position_slot,
    is_flex,
    position_rank,
    nfl_team,
    sum(points) as total_points,
    count(*)::int as num_weeks
from {{ ref("stg__player_weeks") }}
where week != 0
group by all
