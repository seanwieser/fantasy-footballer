select distinct year
from {{ ref("stg_s001__teams") }}
order by year
