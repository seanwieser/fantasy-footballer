select distinct
    matchup_week_map.year,
    matchup_week_map.matchup_week,
    matchup_week_map.week,
    matchups.is_playoff
from {{ ref("stg__settings_matchup_weeks_map") }} as matchup_week_map
inner join {{ ref("base_s001__matchups") }} as matchups
    on
        matchup_week_map.year = matchups.year and
        matchup_week_map.matchup_week = matchups.matchup_week
