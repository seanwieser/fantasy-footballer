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
        unnest( --noqa
            weeks_flat::struct(
                week int,
                lineup struct(
                    playerId varchar,
                    lineupSlot varchar
                )[],
                score_for double,
                outcome varchar,
                opponent varchar
            )
        )
    from team_weeks_unnested
),

team_weeks_enriched as (
    select
        team_weeks.team_id,
        team_weeks.team_year_id,
        team_weeks.team_year_id || '_' || team_weeks.week as team_week_id,
        team_weeks.team_name,
        opponents.team_id as opponent_team_id,
        opponents.team_year_id as opponent_team_year_id,
        opponents.team_year_id || '_' || team_weeks.week as opponent_team_week_id,
        team_weeks.year,
        team_weeks.week,
        team_weeks.lineup,
        team_weeks.score_for,
        team_weeks.outcome
    from team_weeks_expanded as team_weeks
    inner join {{ ref("base_s001__teams") }} as opponents
        on
            team_weeks.opponent = opponents.team_name and
            team_weeks.year = opponents.year
)

select *
from team_weeks_enriched
