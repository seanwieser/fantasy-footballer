select
    roster.owner_id,
    roster.owner_name,
    roster.year,
    roster.player_name,
    roster.position_slot as position,
    roster.nfl_team,
    roster.weeks_held,
    roster.weeks_started,
    round(roster.points_held, 2) as points_held,
    round(roster.points_started, 2) as points_started,
    round(roster.points_held / roster.weeks_held, 2) as avg_points,
    round(player_season.reg_season_points, 2) as player_reg_season_points,
    -- capture_rate: share of the player's *whole regular season* this owner started — low when the
    -- player was only rostered part of the year (acquisition timing), even with perfect deployment.
    if(
        player_season.reg_season_points > 0 and roster.points_started >= 0,
        round(roster.points_started / player_season.reg_season_points, 4),
        null
    ) as capture_rate,
    -- roster_utilization: of the points the player scored *while on this roster*, the share the owner
    -- actually started — pure start/sit deployment (a full-time started player reads ~100%).
    if(
        roster.points_held > 0 and roster.points_started >= 0,
        round(roster.points_started / roster.points_held, 4),
        null
    ) as roster_utilization
from {{ ref("int__owner_player_season") }} as roster
left join {{ ref("int__player_season_stats") }} as player_season
    on roster.player_year_id = player_season.player_year_id
order by roster.points_started desc, roster.points_held desc
