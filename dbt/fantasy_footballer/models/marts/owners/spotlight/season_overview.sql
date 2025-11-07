with season_overview_stats as (
    select
        team_id,
        team_year_id,
        year,
        acquisitions,
        standing,
        trades,
        streak,
        wins || '-' || losses as record,
        round(points_for, 2) as points_for,
        round(points_against, 2) as points_against,
        100 - acquisition_budget_spent as budget
    from {{ ref('base_s001__teams') }}
),

shotguns_by_team as (
    select
        team_id,
        team_year_id,
        year,
        sum(if(is_shotgun, 1, 0)) as shotguns
    from {{ ref("int__shotguns") }}
    group by all
),

season_overview as (
    select
        owner_team_map.owner_id,
        season_overview_stats.year,
        season_overview_stats.record,
        season_overview_stats.acquisitions,
        season_overview_stats.budget,
        season_overview_stats.standing,
        season_overview_stats.trades,
        season_overview_stats.streak,
        clutch_records.record as clutch_record,
        shotguns_by_team.shotguns::int as shotguns,
        round(clutch_records.season_points_for, 2) as points_for,
        round(clutch_records.season_points_for / weeks_played.weeks_played, 2) as points_for_per_week,
        round(clutch_records.season_points_against, 2) as points_against,
        round(clutch_records.season_points_against / weeks_played.weeks_played, 2) as points_against_per_week
    from season_overview_stats
    inner join {{ ref("int__owner_team_map") }} as owner_team_map
        on season_overview_stats.team_id = owner_team_map.team_id
    full outer join {{ ref("int__clutch_records") }} as clutch_records
        on season_overview_stats.team_year_id = clutch_records.team_year_id
    inner join {{ ref("int__weeks_played_by_year") }} as weeks_played
        on season_overview_stats.year = weeks_played.year
    inner join shotguns_by_team
        on season_overview_stats.team_year_id = shotguns_by_team.team_year_id
)

select *
from season_overview
