select distinct nfl_team
from {{ ref("stg__players") }}
order by nfl_team
