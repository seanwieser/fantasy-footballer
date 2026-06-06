with reg_team_weeks as (
    select
        team_weeks.team_week_id,
        team_weeks.team_year_id,
        team_weeks.year,
        team_weeks.week,
        team_weeks.score_for,
        team_weeks.outcome
    from {{ ref("stg__team_weeks") }} as team_weeks
    inner join {{ ref("int__matchup_week_playoff_map") }} as matchup_week_playoff_map
        on
            team_weeks.year = matchup_week_playoff_map.year and
            team_weeks.week = matchup_week_playoff_map.week
    where
        team_weeks.outcome != 'U' and
        not matchup_week_playoff_map.is_playoff
),

week_medians as (
    select
        year,
        week,
        median(score_for) as week_median
    from reg_team_weeks
    group by year, week
),

ranked as (
    select
        reg_team_weeks.*,
        -- teams strictly above me this week = rank in descending order minus 1 (ties share a rank)
        rank() over (partition by reg_team_weeks.year, reg_team_weeks.week order by reg_team_weeks.score_for desc)
        - 1 as teams_above,
        rank() over (partition by reg_team_weeks.year, reg_team_weeks.week order by reg_team_weeks.score_for asc)
        - 1 as teams_below
    from reg_team_weeks
)

select
    ranked.team_week_id,
    ranked.team_year_id,
    ranked.year,
    ranked.week,
    ranked.score_for,
    ranked.outcome = 'W' and ranked.score_for < week_medians.week_median as is_lucky_win,
    ranked.outcome = 'L' and ranked.score_for > week_medians.week_median as is_unlucky_loss,
    case
        when ranked.outcome = 'W' then ranked.teams_above
        when ranked.outcome = 'L' then -ranked.teams_below
        else 0
    end as luck_points
from ranked
inner join week_medians
    on ranked.year = week_medians.year and ranked.week = week_medians.week
