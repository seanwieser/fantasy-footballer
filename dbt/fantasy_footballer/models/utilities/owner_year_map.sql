select distinct
    stg__teams.owner_id,
    owner_display_names.owner_name,
    stg__teams.year
from {{ ref("stg__teams") }} as stg__teams
inner join {{ ref("stg__owner_display_names") }} as owner_display_names
    on stg__teams.owner_id = owner_display_names.owner_id
order by stg__teams.year, stg__teams.owner_id
