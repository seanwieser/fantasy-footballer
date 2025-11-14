{% test assert_model_has_rows(model) %}

select 1
from {{ model }}
having count(*) = 0

{% endtest %}