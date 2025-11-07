select
    year,
    array_agg({ 'owner_id': owner_id, 'owner_name': owner_name }) as owners
from {{ ref("int__owner_team_year_map") }}
group by year
order by year
