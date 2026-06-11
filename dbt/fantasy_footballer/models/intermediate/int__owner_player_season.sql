with roster_weeks as (
    select
        team_year_id,
        player_year_id,
        player_week_id,
        lineup_slot,
        year,
        week
    from {{ ref("stg__team_week_players") }}
),

regular_season_weeks as (
    select roster_weeks.*
    from roster_weeks
    left join {{ ref("int__matchup_week_playoff_map") }} as playoff_map
        on
            roster_weeks.year = playoff_map.year and
            roster_weeks.week = playoff_map.week
    where not coalesce(playoff_map.is_playoff, false)
),

roster_week_points as (
    select
        regular_season_weeks.team_year_id,
        regular_season_weeks.player_year_id,
        regular_season_weeks.lineup_slot,
        regular_season_weeks.year,
        regular_season_weeks.lineup_slot not in ('BE', 'IR') as is_started,
        coalesce(player_weeks.points, 0) as points
    from regular_season_weeks
    left join {{ ref("stg__player_weeks") }} as player_weeks
        on regular_season_weeks.player_week_id = player_weeks.player_week_id
)

select
    owner_map.owner_id,
    owner_map.owner_name,
    owner_map.owner_year_id,
    roster_week_points.year,
    roster_week_points.player_year_id,
    owner_map.owner_id || '_' || roster_week_points.player_year_id as owner_player_year_id,
    players.player_name,
    players.position_slot,
    players.nfl_team,
    count(*)::int as weeks_held,
    count_if(roster_week_points.is_started)::int as weeks_started,
    sum(roster_week_points.points)::double as points_held,
    coalesce(sum(roster_week_points.points) filter (where roster_week_points.is_started), 0)::double
        as points_started
from roster_week_points
inner join {{ ref("int__owner_team_year_map") }} as owner_map
    on roster_week_points.team_year_id = owner_map.team_year_id
inner join {{ ref("base_s001__players") }} as players
    on roster_week_points.player_year_id = players.player_year_id
group by all
