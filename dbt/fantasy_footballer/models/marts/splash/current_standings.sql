with current_season as (
    select
        teams.standing,
        teams.team_name                as name,
        owner_team_map.owner_name      as owner,
        teams.wins,
        teams.losses,
        round(teams.points_for, 2)     as points_for,
        round(teams.points_against, 2) as points_against,
        teams.streak,
        owner_team_map.owner_id
    from {{ ref("base_s001__teams") }} as teams
    left join {{ ref('int__owner_team_year_map') }} as owner_team_map
        on teams.team_year_id = owner_team_map.team_year_id
    cross join {{ ref("int__current_season_year") }} as current_year
    where teams.year = current_year.current_season_year
),

-- Reproduces ESPN's rank during a real season (its `standing` is already a unique 1..N), and
-- assigns a deterministic unique rank in the post-draft/pre-game window where every team is 0-0-0
-- and ESPN leaves `standing` at 0 for all.
ranked as (
    select
        row_number() over (
            order by standing asc, wins desc, points_for desc, name asc
        )::int             as standing,
        name,
        owner,
        wins,
        losses,
        points_for,
        points_against,
        streak,
        owner_id
    from current_season
)

select *
from ranked
order by standing
