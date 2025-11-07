with weeks_played_grouped as (
    select
        team_weeks.year,
        team_weeks.team_year_id,
        team_weeks.outcome != 'U' as is_played,
        count(team_weeks.week) as weeks_ct
    from {{ ref('stg__team_weeks') }} as team_weeks
    inner join {{ ref("int__matchup_week_playoff_map") }} as matchup_week_playoff_map
        on
            team_weeks.year = matchup_week_playoff_map.year and
            team_weeks.week = matchup_week_playoff_map.week
    where not matchup_week_playoff_map.is_playoff
    group by all
),

weeks_played_by_year as (
    select
        year,
        min(weeks_ct) as weeks_played
    from weeks_played_grouped
    where is_played
    group by year
)

select
    year,
    weeks_played::int as weeks_played
from weeks_played_by_year
