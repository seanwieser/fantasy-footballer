{% test test_average_equals(model, column_name, value, tolerance=0.01, allow_null=false) %}

with validation as (
    select
        avg({{ column_name }}) as actual_average,
        {{ value }} as expected_average,
        {{ tolerance }} as tolerance_value,
        count(*) as total_rows,
        count({{ column_name }}) as non_null_rows
    from {{ model }}
    {% if not allow_null %}
    where {{ column_name }} is not null
    {% endif %}
)

select
    actual_average,
    expected_average,
    tolerance_value,
    abs(actual_average - expected_average) as difference
from validation
where
    actual_average is not null
    and abs(actual_average - expected_average) > tolerance_value

{% endtest %}