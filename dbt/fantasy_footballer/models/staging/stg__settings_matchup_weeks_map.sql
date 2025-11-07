with matchup_weeks_unnested as (
    select
        year,
        unnest(matchup_weeks) -- noqa
    from {{ ref("base_s001__settings") }}
),

matchup_weeks_unpivoted as (
    select
        year,
        matchup_week,
        weeks
    from matchup_weeks_unnested
    unpivot (
        weeks for matchup_week in
        ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17")
    )
),

matchup_week_map as (
    select
        year,
        matchup_week,
        unnest(weeks) as week
    from matchup_weeks_unpivoted
)

select
    year,
    matchup_week::int   as matchup_week,
    week::int           as week
from matchup_week_map
