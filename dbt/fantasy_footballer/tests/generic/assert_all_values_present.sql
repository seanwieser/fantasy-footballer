{% test assert_all_values_present(model, column_name, to, field) %}
-- Inverse of a relationships test (which checks child -> parent): every value of `column_name` in this
-- model must appear in `field` of `to`. Used to assert a seed catalog has no orphan rows — every
-- metric_key in the catalog actually produces at least one mart row, catching a seed entry whose
-- candidate branch was never added (or a typo'd key).
select {{ column_name }} as missing_value
from {{ model }}
where {{ column_name }} not in (
    select {{ field }}
    from {{ to }}
    where {{ field }} is not null
)
{% endtest %}
