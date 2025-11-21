with player_stats_unnested as (
    select
        player_id,
        player_year_id,
        nfl_team,
        year,
        player_name,
        position_slot,
        is_flex,
        position_rank,
        unnest(stats_raw) as stats_flat
    from {{ ref("base_s001__players") }}
),

player_stats_expanded as (
    select
        player_stats_unnested.player_id,
        player_stats_unnested.player_year_id,
        player_stats_unnested.player_year_id ||
        '_' || player_stats_unnested.stats_flat['week']::varchar as player_week_id,
        player_stats_unnested.nfl_team,
        player_stats_unnested.player_name,
        player_stats_unnested.year,
        player_stats_unnested.stats_flat['week']::int as week,
        player_stats_unnested.position_slot,
        player_stats_unnested.is_flex,
        player_stats_unnested.position_rank,
        player_stats_unnested.stats_flat['teamWin']::int as team_win,
        player_stats_unnested.stats_flat['points']::double as points,
        player_stats_unnested.stats_flat['receivingReceptions']::double as receiving_receptions,
        player_stats_unnested.stats_flat['receivingYards']::double as receiving_yards,
        player_stats_unnested.stats_flat['receivingTargets']::int as receiving_targets,
        player_stats_unnested.stats_flat['receivingTouchdowns']::int as receiving_touchdowns,
        player_stats_unnested.stats_flat['receiving2PtConversions']::int as receiving_2_pt_conversions,
        player_stats_unnested.stats_flat['rushingAttempts']::int as rushing_attempts,
        player_stats_unnested.stats_flat['rushingYards']::double as rushing_yards,
        player_stats_unnested.stats_flat['rushingTouchdowns']::int as rushing_touchdowns,
        player_stats_unnested.stats_flat['rushing2PtConversions']::int as rushing_2_pt_conversions,
        player_stats_unnested.stats_flat['passingAttempts']::int as passing_attempts,
        player_stats_unnested.stats_flat['passingCompletions']::int as passing_completions,
        player_stats_unnested.stats_flat['passingIncompletions']::int as passing_incompletions,
        player_stats_unnested.stats_flat['passingYards']::double as passing_yards,
        player_stats_unnested.stats_flat['passingTouchdowns']::int as passing_touchdowns,
        player_stats_unnested.stats_flat['passingCompletionPercentage']::double as passing_completion_percentage,
        player_stats_unnested.stats_flat['passingTimesSacked']::int as passing_times_sacked,
        player_stats_unnested.stats_flat['fumbles']::int as fumbles,
        player_stats_unnested.stats_flat['lostFumbles']::int as lost_fumbles,
        player_stats_unnested.stats_flat['turnovers']::int as turnovers,
        player_stats_unnested.stats_flat['madeFieldGoalsFrom40To49']::int as made_field_goals_from_40_to_49,
        player_stats_unnested.stats_flat['attemptedFieldGoalsFrom40To49']::int
            as attempted_field_goals_from_40_to_49,
        player_stats_unnested.stats_flat['madeFieldGoalsFromUnder40']::int as made_field_goals_from_under_40,
        player_stats_unnested.stats_flat['attemptedFieldGoalsFromUnder40']::int
            as attempted_field_goals_from_under_40,
        player_stats_unnested.stats_flat['madeFieldGoals']::int as made_field_goals,
        player_stats_unnested.stats_flat['attemptedFieldGoals']::int as attempted_field_goals,
        player_stats_unnested.stats_flat['madeExtraPoints']::int as made_extra_points,
        player_stats_unnested.stats_flat['attemptedExtraPoints']::int as attempted_extra_points
    from player_stats_unnested
)

select *
from player_stats_expanded
