{%
    set breakdown_fields = [
        {"raw_field": "week", "field": "week","datatype": "integer"},
        {"raw_field": "teamWin", "field": "team_win","datatype": "integer"},
        {"raw_field": "points", "field": "points","datatype": "double"},
        {"raw_field": "receivingReceptions", "field": "receiving_receptions","datatype": "double"},
        {"raw_field": "receivingYards", "field": "receiving_yards","datatype": "double"},
        {"raw_field": "receivingTargets", "field": "receiving_targets","datatype": "integer"},
        {"raw_field": "receivingTouchdowns", "field": "receiving_touchdowns","datatype": "integer"},
        {"raw_field": "receiving2PtConversions", "field": "receiving_2_pt_conversions","datatype": "integer"},
        {"raw_field": "rushingAttempts", "field": "rushing_attempts","datatype": "integer"},
        {"raw_field": "rushingYards", "field": "rushing_yards","datatype": "double"},
        {"raw_field": "rushingTouchdowns", "field": "rushing_touchdowns","datatype": "integer"},
        {"raw_field": "rushing2PtConversions", "field": "rushing_2_pt_conversions","datatype": "integer"},
        {"raw_field": "passingAttempts", "field": "passing_attempts","datatype": "integer"},
        {"raw_field": "passingCompletions", "field": "passing_completions","datatype": "integer"},
        {"raw_field": "passingIncompletions", "field": "passing_incompletions","datatype": "integer"},
        {"raw_field": "passingYards", "field": "passing_yards","datatype": "double"},
        {"raw_field": "passingTouchdowns", "field": "passing_touchdowns","datatype": "integer"},
        {"raw_field": "passingCompletionPercentage", "field": "passing_completion_percentage","datatype": "double"},
        {"raw_field": "passingTimesSacked", "field": "passing_times_sacked","datatype": "integer"},
        {"raw_field": "fumbles", "field": "fumbles","datatype": "integer"},
        {"raw_field": "lostFumbles", "field": "lost_fumbles","datatype": "integer"},
        {"raw_field": "turnovers", "field": "turnovers","datatype": "integer"},
        {"raw_field": "madeFieldGoalsFrom40To49", "field": "made_field_goals_from_40_to_49","datatype": "integer"},
        {"raw_field": "attemptedFieldGoalsFrom40To49", "field": "attempted_field_goals_from_40_to_49","datatype": "integer"},
        {"raw_field": "madeFieldGoalsFromUnder40", "field": "made_field_goals_from_under_40","datatype": "integer"},
        {"raw_field": "attemptedFieldGoalsFromUnder40", "field": "attempted_field_goals_from_under_40","datatype": "integer"},
        {"raw_field": "madeFieldGoals", "field": "made_field_goals","datatype": "integer"},
        {"raw_field": "attemptedFieldGoals", "field": "attempted_field_goals","datatype": "integer"},
        {"raw_field": "madeExtraPoints", "field": "made_extra_points","datatype": "integer"},
        {"raw_field": "attemptedExtraPoints", "field": "attempted_extra_points","datatype": "integer"}
    ]
%}

with player_stats_unnested as (
    select
        player_id,
        year,
        name,
        unnest(stats_raw) as stats_flat
    from {{ ref("stg_s001__players") }}
),

player_stats_expanded as (
    select
        player_id,
        year,
        name,
        player_id || '_' || stats_flat['week']::varchar as player_stat_id,
        {% for breakdown_field in breakdown_fields -%}
            stats_flat['{{ breakdown_field['raw_field'] }}']::{{ breakdown_field['datatype'] }}
                as {{ breakdown_field['field'] }}{% if not loop.last %},{% endif %}
        {% endfor -%}
    from player_stats_unnested
)

select *
from player_stats_expanded
