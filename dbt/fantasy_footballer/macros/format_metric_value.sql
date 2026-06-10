{% macro format_metric_value(value_col, format_col) %}
-- Shared display formatting for the metric-catalog marts (h2h_owner_metrics, all_time_records,
-- season_highlights): renders a numeric metric_value per its seed value_format. Callers wrap this
-- in a coalesce with any metric-specific override (records, ordinals, clutch W-L) they need first.
case
    when {{ format_col }} = 'int' then round({{ value_col }}, 0)::bigint::varchar
    when {{ format_col }} = 'pct' then round({{ value_col }}, 1)::varchar || '%'
    when {{ format_col }} = 'seed' then '#' || round({{ value_col }}, 0)::bigint::varchar || ' seed'
    else round({{ value_col }}, 2)::varchar
end
{% endmacro %}
