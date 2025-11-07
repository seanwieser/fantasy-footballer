with team_week_lineup_unnested as (
    select
        team_id,
        team_year_id,
        team_name,
        team_week_id,
        opponent_team_id,
        opponent_team_year_id,
        opponent_team_week_id,
        year,
        week,
        unnest(lineup) as lineup_flat
    from {{ ref('stg__team_weeks') }}
    where outcome != 'U'
),

team_week_lineup_player_expanded as (
    select
        team_id,
        team_year_id,
        team_name,
        team_week_id,
        opponent_team_id,
        opponent_team_year_id,
        opponent_team_week_id,
        year,
        week,
        unnest(lineup_flat::struct(playerId varchar, lineupSlot varchar)) as lineup_player_unnested
    from team_week_lineup_unnested
)

select
    team_id,
    team_year_id,
    team_name,
    team_week_id,
    opponent_team_id,
    opponent_team_year_id,
    opponent_team_week_id,
    playerid as player_id,
    playerid || '_' || year as player_year_id,
    playerid || '_' || year || '_' || week as player_week_id,
    if(lineupslot = 'RB/WR/TE', 'FLEX', lineupslot) as lineup_slot,
    year,
    week
from team_week_lineup_player_expanded
