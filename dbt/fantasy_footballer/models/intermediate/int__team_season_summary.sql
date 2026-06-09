with team_stats as (
    select
        team_id,
        team_year_id,
        year,
        acquisitions,
        standing,
        trades,
        streak,
        wins || '-' || losses as record,
        100 - acquisition_budget_spent as budget
    from {{ ref("base_s001__teams") }}
),

summary as (
    select
        team_stats.team_id,
        team_stats.team_year_id,
        team_stats.year,
        owner_map.owner_id,
        team_stats.record,
        team_stats.acquisitions,
        team_stats.budget,
        team_stats.standing,
        team_stats.trades,
        team_stats.streak,
        clutch.record as clutch_record,
        shotgun_counts.shotgun_count as shotguns,
        round(scoring.reg_points_total, 2) as points_for,
        round(scoring.reg_points_total / weeks.weeks_played, 2) as points_for_per_week,
        round(scoring.reg_points_against, 2) as points_against,
        round(scoring.reg_points_against / weeks.weeks_played, 2) as points_against_per_week
    from team_stats
    left join {{ ref("int__clutch_records") }} as clutch
        on team_stats.team_year_id = clutch.team_year_id
    inner join {{ ref("int__owner_team_year_map") }} as owner_map
        on team_stats.team_year_id = owner_map.team_year_id
    inner join {{ ref("int__owner_season_scoring") }} as scoring
        on team_stats.team_year_id = scoring.team_year_id
    inner join {{ ref("int__weeks_played_by_year") }} as weeks
        on team_stats.year = weeks.year
    inner join {{ ref("int__team_shotgun_counts") }} as shotgun_counts
        on team_stats.team_year_id = shotgun_counts.team_year_id
)

select * from summary
