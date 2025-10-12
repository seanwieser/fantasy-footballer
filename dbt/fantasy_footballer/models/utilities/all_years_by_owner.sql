select distinct
    owner_id,
    year
from {{ ref("stg_s001__teams") }}
order by year, owner_id
