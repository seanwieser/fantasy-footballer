with player_weeks as (
    select
        player_weeks.year,
        player_weeks.player_year_id,
        player_weeks.player_name,
        player_weeks.position_slot,
        player_weeks.is_flex,
        player_weeks.position_rank,
        player_weeks.nfl_team,
        player_weeks.points,
        playoff_map.is_playoff
    from {{ ref("stg__player_weeks") }} as player_weeks
    left join {{ ref("int__matchup_week_playoff_map") }} as playoff_map
        on
            player_weeks.year = playoff_map.year and
            player_weeks.week = playoff_map.week
    where player_weeks.week != 0
)

select
    year,
    player_year_id,
    player_name,
    position_slot,
    is_flex,
    position_rank,
    nfl_team,
    sum(points) as total_points,
    -- regular-season weeks only (in the matchup map and not a playoff week); excludes fantasy
    -- playoff weeks and any NFL weeks beyond the fantasy season (e.g. week 18, absent from the map)
    sum(points) filter (where is_playoff = false) as reg_season_points,
    count(*)::int as num_weeks
from player_weeks
group by all
