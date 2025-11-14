{% test test_range(model, column_name, min_value, max_value, inclusive=true, allow_null=false) %}

select
    {{ column_name }} as value,
    {{ min_value }} as min_value,
    {{ max_value }} as max_value
from {{ model }}
where
    {% if not allow_null %}
    ({{ column_name }} is null
    {% if inclusive %}
    or {{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }})
    {% else %}
    or {{ column_name }} <= {{ min_value }} or {{ column_name }} >= {{ max_value }})
    {% endif %}
    {% else %}
    {{ column_name }} is not null
    {% if inclusive %}
    and ({{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }})
    {% else %}
    and ({{ column_name }} <= {{ min_value }} or {{ column_name }} >= {{ max_value }})
    {% endif %}
    {% endif %}

{% endtest %}