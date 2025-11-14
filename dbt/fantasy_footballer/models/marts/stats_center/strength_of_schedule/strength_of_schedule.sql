select
    sos_table.year,
    owner_team_map.owner_name,
    round(sos_table.sos, 4) as sos,
    round(sos_table.sosr, 4) as sosr
from {{ ref("int__strength_of_schedule") }} as sos_table
inner join {{ ref("int__owner_team_year_map") }} as owner_team_map
    on sos_table.team_year_id = owner_team_map.team_year_id
