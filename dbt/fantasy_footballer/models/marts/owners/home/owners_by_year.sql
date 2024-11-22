select
    year,
    array_agg({ 'owner_id': owner_id, 'owner_name': owner_name }) as owners
from {{ ref("stg_s001__teams") }}
group by year
order by year
