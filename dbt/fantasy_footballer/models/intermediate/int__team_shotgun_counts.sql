select
    team_id,
    team_year_id,
    year,
    count_if(is_shotgun)::int as shotgun_count,
    list_sort(array_agg(week) filter (where is_shotgun)) as shotgun_weeks
from {{ ref("int__shotguns") }}
group by team_id, team_year_id, year
