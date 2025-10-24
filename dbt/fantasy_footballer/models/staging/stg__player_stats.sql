with player_stats_unnested as (
    select
        owner_year_id,
        player_year_id,
        player_id,
        owner_id,
        owner_name,
        team_name,
        nfl_team,
        year,
        player_name,
        position_slot,
        is_flex,
        position_rank,
        unnest(stats_raw) as stats_flat
    from {{ ref("stg__players") }}
),

player_stats_expanded as (
    select
        player_stats_unnested.player_year_id ||
        '_' || player_stats_unnested.stats_flat['week']::varchar as player_matchup_id,
        player_stats_unnested.owner_year_id ||
        '_' || player_stats_unnested.stats_flat['week']::varchar as owner_matchup_id,
        player_stats_unnested.owner_year_id,
        player_stats_unnested.player_id,
        player_stats_unnested.owner_id,
        player_stats_unnested.owner_name,
        player_stats_unnested.team_name,
        player_stats_unnested.nfl_team,
        player_stats_unnested.player_name,
        player_stats_unnested.year,
        player_stats_unnested.stats_flat['week']::integer as week,
        playoff_matchups.is_playoff,
        player_stats_unnested.position_slot,
        player_stats_unnested.is_flex,
        player_stats_unnested.position_rank,
        player_stats_unnested.stats_flat['teamWin']::integer as team_win,
        player_stats_unnested.stats_flat['points']::double as points,
        player_stats_unnested.stats_flat['receivingReceptions']::double as receiving_receptions,
        player_stats_unnested.stats_flat['receivingYards']::double as receiving_yards,
        player_stats_unnested.stats_flat['receivingTargets']::integer as receiving_targets,
        player_stats_unnested.stats_flat['receivingTouchdowns']::integer as receiving_touchdowns,
        player_stats_unnested.stats_flat['receiving2PtConversions']::integer as receiving_2_pt_conversions,
        player_stats_unnested.stats_flat['rushingAttempts']::integer as rushing_attempts,
        player_stats_unnested.stats_flat['rushingYards']::double as rushing_yards,
        player_stats_unnested.stats_flat['rushingTouchdowns']::integer as rushing_touchdowns,
        player_stats_unnested.stats_flat['rushing2PtConversions']::integer as rushing_2_pt_conversions,
        player_stats_unnested.stats_flat['passingAttempts']::integer as passing_attempts,
        player_stats_unnested.stats_flat['passingCompletions']::integer as passing_completions,
        player_stats_unnested.stats_flat['passingIncompletions']::integer as passing_incompletions,
        player_stats_unnested.stats_flat['passingYards']::double as passing_yards,
        player_stats_unnested.stats_flat['passingTouchdowns']::integer as passing_touchdowns,
        player_stats_unnested.stats_flat['passingCompletionPercentage']::double as passing_completion_percentage,
        player_stats_unnested.stats_flat['passingTimesSacked']::integer as passing_times_sacked,
        player_stats_unnested.stats_flat['fumbles']::integer as fumbles,
        player_stats_unnested.stats_flat['lostFumbles']::integer as lost_fumbles,
        player_stats_unnested.stats_flat['turnovers']::integer as turnovers,
        player_stats_unnested.stats_flat['madeFieldGoalsFrom40To49']::integer as made_field_goals_from_40_to_49,
        player_stats_unnested.stats_flat['attemptedFieldGoalsFrom40To49']::integer
            as attempted_field_goals_from_40_to_49,
        player_stats_unnested.stats_flat['madeFieldGoalsFromUnder40']::integer as made_field_goals_from_under_40,
        player_stats_unnested.stats_flat['attemptedFieldGoalsFromUnder40']::integer
            as attempted_field_goals_from_under_40,
        player_stats_unnested.stats_flat['madeFieldGoals']::integer as made_field_goals,
        player_stats_unnested.stats_flat['attemptedFieldGoals']::integer as attempted_field_goals,
        player_stats_unnested.stats_flat['madeExtraPoints']::integer as made_extra_points,
        player_stats_unnested.stats_flat['attemptedExtraPoints']::integer as attempted_extra_points
    from player_stats_unnested
    inner join {{ ref("playoff_matchups") }} as playoff_matchups
        on
            player_stats_unnested.year = playoff_matchups.year and
            player_stats_unnested.stats_flat['week']::integer = playoff_matchups.week
)

select *
from player_stats_expanded
