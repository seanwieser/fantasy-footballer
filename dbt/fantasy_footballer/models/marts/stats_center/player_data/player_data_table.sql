with player_stats_agg as (
    select
        player_weeks.year,
        player_weeks.player_year_id,
        player_weeks.player_name,
        player_weeks.position_slot,
        player_weeks.is_flex,
        player_weeks.position_rank,
        player_weeks.nfl_team,
        sum(player_weeks.points) as total_points,
        count(*) as num_weeks
    from {{ ref("stg__player_weeks") }} as player_weeks
    where player_weeks.week != 0
    group by all
)

select
    player_stats_agg.year,
    player_stats_agg.player_name,
    player_stats_agg.position_slot as position,
    player_stats_agg.is_flex,
    player_stats_agg.position_rank,
    player_stats_agg.nfl_team,
    round(total_points, 2)              as total_points,
    round(total_points / player_stats_agg.num_weeks, 2)  as avg_points
from player_stats_agg
order by total_points desc
