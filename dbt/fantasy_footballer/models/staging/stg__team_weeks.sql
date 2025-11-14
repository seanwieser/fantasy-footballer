with team_weeks_unnested as (
    select
        team_id,
        team_year_id,
        team_name,
        year,
        unnest(weeks_raw) as weeks_flat
    from {{ ref("base_s001__teams") }}
),

team_weeks_expanded as (
    select
        team_id,
        team_year_id,
        team_name,
        year,
        unnest(weeks_flat)
    from team_weeks_unnested
),

team_weeks_enriched as (
    select
        team_id,
        team_year_id,
        team_year_id || '_' || week as team_week_id,
        team_name,
        opponent_team_id,
        opponent_team_id || '_' || year opponent_team_year_id,
        opponent_team_id || '_' || year || '_' || week as opponent_team_week_id,
        year,
        week,
        lineup,
        score_for,
        outcome
    from team_weeks_expanded
)

select *
from team_weeks_enriched
