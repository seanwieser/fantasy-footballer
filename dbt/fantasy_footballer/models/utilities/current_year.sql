with current_year as (
    select max(year) as this
    from {{ ref("all_years_by_owner") }}
)

select *
from current_year
