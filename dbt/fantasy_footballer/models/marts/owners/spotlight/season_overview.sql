with season_overview_wo_clutch as (
    select
        team_id,
        owner_id,
        year,
        acquisitions,
        standing,
        trades,
        streak,
        wins || '-' || losses as record,
        round(points_for, 2) as points_for,
        round(points_against, 2) as points_against,
        100 - acquisition_budget_spent as budget
    from {{ ref('stg_s001__teams') }}
),

clutch_record_grouped as (
    select
        team_schedules.team_id,
        team_schedules.owner_id,
        team_schedules.year,
        team_schedules.outcome,
        sum(team_schedules.score_for) as season_points_for_by_outcome,
        sum(opponent_schedules.score_for) as season_points_against_by_outcome,
        count_if(abs(team_schedules.score_for - opponent_schedules.score_for) < 10) as clutch_count
    from {{ ref('stg_s001__team_schedules') }} as team_schedules
    inner join {{ ref('stg_s001__team_schedules') }} as opponent_schedules
        on team_schedules.opponent_team_schedule_id = opponent_schedules.team_schedule_id
    where team_schedules.outcome != 'U' and not team_schedules.is_playoff
    group by all
),

clutch_record_no_zeroes as (
    select
        team_id,
        owner_id,
        year,
        sum(season_points_for_by_outcome) as season_points_for,
        sum(season_points_against_by_outcome) as season_points_against,
        replace(replace(string_agg(
            outcome || clutch_count, ''
            order by outcome desc
        ), '-', ''), 'L', '-') as record
    from clutch_record_grouped
    group by all
),

clutch_record as (
    select
        team_id,
        owner_id,
        year,
        season_points_for,
        season_points_against,
        case
            when starts_with(record, '-') then '0' || record
            when starts_with(record, 'W') and not contains(record, '-') then replace(record, 'W', '') || '-0'
            else coalesce(replace(record, 'W', ''), '0-0')
        end as record
    from clutch_record_no_zeroes
),

weeks_played_grouped as (
    select
        year,
        team_id,
        outcome != 'U' as is_played,
        count(week) as weeks_ct
    from main_staging.stg_s001__team_schedules
    where not is_playoff
    group by all
),

weeks_played as (
    select
        year,
        min(weeks_ct) as weeks_played
    from weeks_played_grouped
    where is_played
    group by year
),

shotguns_by_team as (
    select
        team_id,
        count(is_shotgun) as shotguns
    from {{ ref("int_shotguns") }}
    group by team_id
),

season_overview as (
    select
        season_overview_wo_clutch.owner_id,
        season_overview_wo_clutch.year,
        season_overview_wo_clutch.record,
        season_overview_wo_clutch.acquisitions,
        season_overview_wo_clutch.budget,
        season_overview_wo_clutch.standing,
        season_overview_wo_clutch.trades,
        season_overview_wo_clutch.streak,
        clutch_record.record as clutch_record,
        shotguns_by_team.shotguns,
        round(clutch_record.season_points_for, 2) as points_for,
        round(clutch_record.season_points_for / weeks_played.weeks_played, 2) as points_for_per_week,
        round(clutch_record.season_points_against, 2) as points_against,
        round(clutch_record.season_points_against / weeks_played.weeks_played, 2) as points_against_per_week
    from season_overview_wo_clutch
    full outer join clutch_record
        on season_overview_wo_clutch.team_id = clutch_record.team_id
    inner join weeks_played
        on season_overview_wo_clutch.year = weeks_played.year
    inner join shotguns_by_team
        on season_overview_wo_clutch.team_id = shotguns_by_team.team_id
)

select *
from season_overview
