select current_season_year as year
from {{ ref("int__current_season_year") }}
