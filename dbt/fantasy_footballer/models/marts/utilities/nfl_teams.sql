select distinct nfl_team
from {{ ref("base_s001__players") }}
order by nfl_team
