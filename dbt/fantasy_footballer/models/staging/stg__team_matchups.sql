with team_matchups_unnested as (
    select
        owner_year_id,
        year,
        owner_id,
        unnest(matchups_raw) as matchups_flat
    from {{ ref("stg__teams") }}
),

team_matchups_expanded as (
    select
        owner_year_id,
        year,
        owner_id,
        unnest(matchups_flat::struct(week int, score_for double, outcome varchar, opponent varchar)) -- noqa
    from team_matchups_unnested
),

team_matchups_with_opponent_ids as (
    select
        matchups.owner_year_id || '_' || matchups.week as owner_matchup_id,
        matchups.owner_year_id,
        matchups.owner_id,
        opponents.owner_year_id as opponent_owner_year_id,
        opponents.owner_year_id || '_' || matchups.week as opponent_owner_matchup_id,
        matchups.year,
        matchups.week,
        matchups.score_for,
        matchups.outcome,
        playoff_matchups.is_playoff
    from team_matchups_expanded as matchups
    inner join {{ ref("stg__teams") }} as opponents
        on matchups.opponent = opponents.team_name and matchups.year = opponents.year
    inner join {{ ref("playoff_matchups") }} as playoff_matchups
        on
            matchups.year = playoff_matchups.year and
            matchups.week = playoff_matchups.week
)

select *
from team_matchups_with_opponent_ids
