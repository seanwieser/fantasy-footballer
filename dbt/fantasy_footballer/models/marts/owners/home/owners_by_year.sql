select
    year,
    array_agg({ 'owner_id': owner_id, 'owner_name': owner_name }) as owners
from {{ ref("stg__teams") }}
group by year
order by year
