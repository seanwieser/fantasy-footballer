with owner_season as (
    select
        owner_map.owner_id,
        owner_map.owner_name,
        owner_map.owner_year_id,
        optimal_lineups.team_year_id,
        owner_map.year,
        sum(optimal_lineups.actual_points) as actual_points,
        sum(optimal_lineups.optimal_points) as optimal_points
    from {{ ref("int__optimal_lineups") }} as optimal_lineups
    inner join {{ ref("int__owner_team_year_map") }} as owner_map
        on optimal_lineups.team_year_id = owner_map.team_year_id
    group by all
)

select
    owner_id,
    owner_name,
    owner_year_id,
    team_year_id,
    year,
    round(actual_points, 2) as actual_points,
    round(optimal_points, 2) as optimal_points,
    round(optimal_points - actual_points, 2) as points_left_on_table,
    round(actual_points / nullif(optimal_points, 0), 4) as lineup_efficiency
from owner_season
