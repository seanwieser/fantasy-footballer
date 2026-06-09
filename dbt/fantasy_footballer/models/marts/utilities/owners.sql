with owner_years as (
    select
        owner_id,
        owner_name,
        year
    from {{ ref("int__owner_team_year_map") }}
),

owner_activity as (
    select
        owner_id,
        max(owner_name) as owner_name,
        min(year) as first_year,
        max(year) as last_year,
        count(distinct year) as seasons_played
    from owner_years
    group by owner_id
)

select
    owner_activity.owner_id::int as owner_id,
    owner_activity.owner_name::varchar as owner_name,
    owner_activity.first_year::int as first_year,
    owner_activity.last_year::int as last_year,
    owner_activity.seasons_played::int as seasons_played,
    -- An owner is active if they fielded a team in the current season; retired otherwise.
    (owner_activity.last_year = current_year.current_season_year)::boolean as is_active
from owner_activity
cross join {{ ref("int__current_season_year") }} as current_year
order by owner_activity.owner_id
