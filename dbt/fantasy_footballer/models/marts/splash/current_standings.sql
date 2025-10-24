with current_standings as (
    select
        teams.standing,
        teams.team_name                as name,
        teams.owner_name               as owner,
        teams.wins,
        teams.losses,
        round(teams.points_for, 2)     as points_for,
        round(teams.points_against, 2) as points_against,
        teams.streak
    from {{ ref("stg__teams") }} as teams
    cross join {{ ref("current_year") }} as current_year
    where teams.year = current_year.this
    order by teams.standing
)

select *
from current_standings
