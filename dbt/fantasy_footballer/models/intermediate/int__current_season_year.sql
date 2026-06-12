-- "Current season" = the latest season that has been drafted. The fantasy year begins at the draft,
-- so that's the right pivot for every "current" mart. ESPN exposes the upcoming season as an
-- all-zero shell before its draft, so plain `max(year)` over teams would flip "current" to a season
-- that hasn't started; draft picks only exist once a league has actually drafted.
select max(year) as current_season_year
from {{ ref("base_s001__draftpicks") }}
