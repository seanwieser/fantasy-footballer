with current_year as (
    select max(year) as this
    from {{ ref("owner_year_map") }}
)

select *
from current_year
