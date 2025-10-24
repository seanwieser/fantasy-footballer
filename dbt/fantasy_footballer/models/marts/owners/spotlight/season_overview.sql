with season_overview_wo_clutch as (
    select
        owner_year_id,
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
    from {{ ref('stg__teams') }}
),

clutch_record_grouped as (
    select
        team_matchups.owner_year_id,
        team_matchups.owner_id,
        team_matchups.year,
        team_matchups.outcome,
        sum(team_matchups.score_for) as season_points_for_by_outcome,
        sum(opponent_matchups.score_for) as season_points_against_by_outcome,
        count_if(abs(team_matchups.score_for - opponent_matchups.score_for) < 10) as clutch_count
    from {{ ref('stg__team_matchups') }} as team_matchups
    inner join {{ ref('stg__team_matchups') }} as opponent_matchups
        on team_matchups.opponent_owner_matchup_id = opponent_matchups.owner_matchup_id
    where team_matchups.outcome != 'U' and not team_matchups.is_playoff
    group by all
),

clutch_record_no_zeroes as (
    select
        owner_year_id,
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
        owner_year_id,
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
        owner_year_id,
        outcome != 'U' as is_played,
        count(week) as weeks_ct
    from {{ ref('stg__team_matchups') }}
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
        owner_year_id,
        owner_id,
        year,
        sum(if(is_shotgun, 1, 0)) as shotguns
    from {{ ref("int_shotguns") }}
    group by all
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
        shotguns_by_team.shotguns::int as shotguns,
        round(clutch_record.season_points_for, 2) as points_for,
        round(clutch_record.season_points_for / weeks_played.weeks_played, 2) as points_for_per_week,
        round(clutch_record.season_points_against, 2) as points_against,
        round(clutch_record.season_points_against / weeks_played.weeks_played, 2) as points_against_per_week
    from season_overview_wo_clutch
    full outer join clutch_record
        on season_overview_wo_clutch.owner_year_id = clutch_record.owner_year_id
    inner join weeks_played
        on season_overview_wo_clutch.year = weeks_played.year
    inner join shotguns_by_team
        on season_overview_wo_clutch.owner_year_id = shotguns_by_team.owner_year_id
)

select *
from season_overview
