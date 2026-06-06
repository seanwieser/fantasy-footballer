select distinct
    owner_id,
    owner_name,
    year
from {{ ref("int__owner_team_year_map") }}
order by year, owner_id
