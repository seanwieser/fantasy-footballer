with base as (
    select distinct
        team_weeks.year,
        team_weeks.team_year_id,
        team_weeks.opponent_team_year_id,
        count(team_weeks.team_year_id)
        filter (where team_weeks.outcome != 'U')
            over (partition by team_weeks.team_year_id) as games_played_total,
        count(team_weeks.opponent_team_year_id)
        filter (where team_weeks.outcome != 'U')
            over (partition by team_weeks.team_year_id, team_weeks.opponent_team_year_id) as times_played_opponent,
        array_length(
            list_filter(
                opponent_teams.weeks_raw,
                lambda x: --noqa
                x.opponent_team_id || '_' || team_weeks.year != team_weeks.team_year_id and --noqa
                x.outcome = 'W' and --noqa
                x.week <= league_settings.reg_season_count --noqa
            )
        ) as opponent_wins_against_others,
        array_length(
            list_filter(
                opponent_teams.weeks_raw,
                lambda x: --noqa
                x.opponent_team_id || '_' || team_weeks.year != team_weeks.team_year_id and --noqa
                x.outcome != 'U' and --noqa
                x.week <= league_settings.reg_season_count --noqa
            )
        ) as opponent_games_against_others
    from {{ ref("stg__team_weeks") }} as team_weeks
    inner join {{ ref("base_s001__teams") }} as opponent_teams
        on team_weeks.opponent_team_year_id = opponent_teams.team_year_id
    inner join {{ ref("base_s001__settings") }} as league_settings
        on team_weeks.year = league_settings.year
    where team_weeks.week <= league_settings.reg_season_count
    qualify times_played_opponent > 0
),

ow as (
    select
        year,
        team_year_id,
        opponent_team_year_id,
        games_played_total,
        times_played_opponent,
        sum(times_played_opponent * (opponent_wins_against_others / opponent_games_against_others))
            over (partition by team_year_id)
        /
        games_played_total as ow
    from base
),

oow_parts as (
    select distinct
        team_ow.year,
        team_ow.team_year_id,
        team_ow.opponent_team_year_id,
        team_ow.games_played_total,
        team_ow.ow,
        team_ow.times_played_opponent * opponent_ow.ow as oow_part_by_opponent
    from ow as team_ow
    inner join ow as opponent_ow
        on team_ow.opponent_team_year_id = opponent_ow.team_year_id
),

oow as (
    select distinct
        year,
        team_year_id,
        ow,
        sum(oow_part_by_opponent) over (partition by team_year_id) / games_played_total as oow
    from oow_parts
)

select
    year,
    team_year_id,
    ow,
    oow,
    (2/3)*ow + (1/3)*oow as sos
from oow
order by sos desc
