with current_year as (
    select max(year) as this
    from {{ ref('all_years') }}
)

select *
from current_year
