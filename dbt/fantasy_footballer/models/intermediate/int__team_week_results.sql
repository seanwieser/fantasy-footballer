with team_weeks as (
    select * from {{ ref("stg__team_weeks") }}
),

results as (
    select
        team_weeks.team_id,
        team_weeks.team_year_id,
        team_weeks.team_week_id,
        team_weeks.year,
        team_weeks.week,
        owner_map.owner_id,
        owner_map.owner_name,
        opponent_owner_map.owner_id as opponent_owner_id,
        opponent_owner_map.team_name as opponent_team_name,
        opponent_owner_map.owner_name as opponent_owner_name,
        team_weeks.score_for,
        opponent_weeks.score_for as score_against,
        team_weeks.outcome,
        abs(team_weeks.score_for - opponent_weeks.score_for) as margin,
        abs(team_weeks.score_for - opponent_weeks.score_for) < 10 and team_weeks.outcome in ('W', 'L') as is_clutch,
        coalesce(shotguns.is_shotgun, false) as is_shotgun,
        playoff_map.is_playoff
    from team_weeks
    inner join team_weeks as opponent_weeks
        on team_weeks.opponent_team_week_id = opponent_weeks.team_week_id
    left join {{ ref("int__owner_team_year_map") }} as owner_map
        on team_weeks.team_year_id = owner_map.team_year_id
    left join {{ ref("int__owner_team_year_map") }} as opponent_owner_map
        on opponent_weeks.team_year_id = opponent_owner_map.team_year_id
    left join {{ ref("int__matchup_week_playoff_map") }} as playoff_map
        on team_weeks.year = playoff_map.year and team_weeks.week = playoff_map.week
    left join {{ ref("int__shotguns") }} as shotguns
        on team_weeks.team_week_id = shotguns.team_week_id
)

select * from results
