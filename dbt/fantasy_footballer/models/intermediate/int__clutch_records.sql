with clutch_records_grouped as (
    select
        team_weeks.team_id,
        team_weeks.team_year_id,
        team_weeks.year,
        team_weeks.outcome,
        sum(team_weeks.score_for) as season_points_for_by_outcome,
        sum(opponent_weeks.score_for) as season_points_against_by_outcome,
        count_if(abs(team_weeks.score_for - opponent_weeks.score_for) < 10) as clutch_count
    from {{ ref('stg__team_weeks') }} as team_weeks
    inner join {{ ref('stg__team_weeks') }} as opponent_weeks
        on team_weeks.opponent_team_week_id = opponent_weeks.team_week_id
    inner join {{ ref("int__matchup_week_playoff_map") }} as matchup_week_playoff_map
        on
            team_weeks.year = matchup_week_playoff_map.year and
            team_weeks.week = matchup_week_playoff_map.week
    where team_weeks.outcome != 'U' and not matchup_week_playoff_map.is_playoff
    group by all
),

clutch_records_no_zeroes as (
    select
        team_id,
        team_year_id,
        year,
        sum(season_points_for_by_outcome) as season_points_for,
        sum(season_points_against_by_outcome) as season_points_against,
        replace(replace(string_agg(
            outcome || clutch_count, ''
            order by outcome desc
        ), '-', ''), 'L', '-') as record
    from clutch_records_grouped
    group by all
),

clutch_records as (
    select
        team_id,
        team_year_id,
        year,
        season_points_for,
        season_points_against,
        case
            when starts_with(record, '-') then '0' || record
            when starts_with(record, 'W') and not contains(record, '-') then replace(record, 'W', '') || '-0'
            else coalesce(replace(record, 'W', ''), '0-0')
        end as record
    from clutch_records_no_zeroes
)

select *
from clutch_records
