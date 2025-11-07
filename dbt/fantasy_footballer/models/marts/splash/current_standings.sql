with current_standings as (
    select
        teams.standing,
        teams.team_name                as name,
        owner_team_map.owner_name      as owner,
        teams.wins,
        teams.losses,
        round(teams.points_for, 2)     as points_for,
        round(teams.points_against, 2) as points_against,
        teams.streak
    from {{ ref("base_s001__teams") }} as teams
    left join {{ ref('int__owner_team_year_map') }} as owner_team_map
        on teams.team_year_id = owner_team_map.team_year_id
    cross join {{ ref("int__current_season_year") }} as current_year
    where teams.year = current_year.current_season_year
    order by teams.standing
)

select *
from current_standings
