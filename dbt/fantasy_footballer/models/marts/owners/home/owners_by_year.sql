-- Powers the per-season owner grid on /owner_history, so it is scoped to seasons that have actually
-- been played — the upcoming drafted-but-unplayed season has no owner-history to render.
with played_seasons as (
    select year
    from {{ ref("int__weeks_played_by_year") }}
)

select
    owner_map.year,
    array_agg({ 'owner_id': owner_map.owner_id, 'owner_name': owner_map.owner_name }) as owners
from {{ ref("int__owner_team_year_map") }} as owner_map
inner join played_seasons on owner_map.year = played_seasons.year
group by owner_map.year
order by owner_map.year
