with current_standings as (
    select
        teams.standing                 as "Standing",
        teams.team_name                as "Name",
        teams.owner_name               as "Owner",
        teams.wins                     as "Wins",
        teams.losses                   as "Losses",
        round(teams.points_for, 2)     as "Points For",
        round(teams.points_against, 2) as "Points Against",
        teams.streak                   as "Streak"
    from {{ ref("stg_s001__teams") }} as teams
    cross join {{ ref("current_year") }} as current_year
    where teams.year = current_year.this
    order by teams.standing
)

select *
from current_standings
