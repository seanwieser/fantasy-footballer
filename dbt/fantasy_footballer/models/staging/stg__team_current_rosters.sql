with team_rosters_unnested as (
    select
        owner_year_id,
        owner_id,
        owner_name,
        team_name,
        unnest(roster) as player_id,
        player_id || '_' || year::varchar as player_year_id,
        year
    from {{ ref("stg__teams") }}
)

select *
from team_rosters_unnested
