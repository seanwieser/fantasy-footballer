select max(year) as current_season_year
from {{ ref("int__owner_team_year_map") }}
