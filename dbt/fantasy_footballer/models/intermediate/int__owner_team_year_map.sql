select distinct
    owner_display_names.owner_id,
    owner_display_names.owner_name,
    owner_display_names.owner_id || '_' || teams.year as owner_year_id,
    teams.team_id,
    teams.team_id || '_' || teams.year as team_year_id,
    teams.team_name,
    teams.year
from {{ ref("base_s001__teams") }} as teams
inner join {{ ref("stg__owner_display_names") }} as owner_display_names
    on teams.display_name = owner_display_names.display_name
order by
    teams.year,
    owner_display_names.owner_id
