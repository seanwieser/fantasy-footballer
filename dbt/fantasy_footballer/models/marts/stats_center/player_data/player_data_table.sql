with player_stats_agg as (
    select
        year,
        player_name,
        position_slot,
        is_flex,
        position_rank,
        nfl_team,
        owner_name,
        team_name,
        is_playoff,
        sum(points) as total_points,
        count(*) as num_weeks
    from {{ ref("stg__player_stats") }}
    group by all
    order by total_points desc
)

select
    year,
    player_name,
    position_slot as position,
    is_flex,
    position_rank,
    nfl_team,
    coalesce(owner_name, '') as owner_name,
    coalesce(team_name, 'Available') as team_name,
    is_playoff,
    round(total_points, 2) as total_points,
    round(total_points / num_weeks, 2) as avg_points
from player_stats_agg
