select distinct
    owner_id,
    owner_name,
    team_id
from {{ ref("int__owner_team_year_map") }}
