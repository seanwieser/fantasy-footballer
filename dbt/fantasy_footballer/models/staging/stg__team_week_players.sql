-- One row per team-(NFL week)-player. The roster is captured per NFL week (a matchup period can span
-- two NFL weeks in the 2018-2019 playoffs), so this unnests stg__team_weeks.lineups (per-NFL-week
-- rosters) and carries both `matchup_week` (the scoring period) and `week` (the NFL week the slot/points
-- belong to). `week`/the ids are NFL-week-based so they pair 1:1 with stg__player_weeks.
with team_matchup_weeks as (
    select
        team_id,
        team_year_id,
        team_name,
        opponent_team_id,
        opponent_team_year_id,
        year,
        week as matchup_week,
        lineups
    from {{ ref('stg__team_weeks') }}
    where outcome != 'U'
),

team_nfl_weeks as (
    select
        team_id,
        team_year_id,
        team_name,
        opponent_team_id,
        opponent_team_year_id,
        year,
        matchup_week,
        unnest(lineups) as week_lineup
    from team_matchup_weeks
),

team_nfl_week_rosters as (
    select
        team_id,
        team_year_id,
        team_name,
        opponent_team_id,
        opponent_team_year_id,
        year,
        matchup_week,
        -- struct expands to `week` (NFL) + `players`
        unnest(week_lineup) as week_roster
    from team_nfl_weeks
),

team_nfl_week_players as (
    select
        team_id,
        team_year_id,
        team_name,
        opponent_team_id,
        opponent_team_year_id,
        year,
        matchup_week,
        week,
        unnest(players) as player_struct
    from team_nfl_week_rosters
),

expanded as (
    select
        team_id,
        team_year_id,
        team_name,
        opponent_team_id,
        opponent_team_year_id,
        year,
        matchup_week,
        week,
        -- struct expands to `playerId` + `lineupSlot`
        unnest(player_struct) as player_fields
    from team_nfl_week_players
)

select
    team_id,
    team_year_id,
    team_name,
    team_year_id || '_' || week as team_week_id,
    opponent_team_id,
    opponent_team_year_id,
    opponent_team_id || '_' || year || '_' || week as opponent_team_week_id,
    playerid as player_id,
    playerid || '_' || year as player_year_id,
    playerid || '_' || year || '_' || week as player_week_id,
    if(lineupslot = 'RB/WR/TE', 'FLEX', lineupslot) as lineup_slot,
    year,
    matchup_week,
    week
from expanded
