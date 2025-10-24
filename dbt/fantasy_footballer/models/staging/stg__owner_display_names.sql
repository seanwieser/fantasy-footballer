select
    owner_names.owner_id,
    owner_names.owner_name,
    display_names.display_name
from {{ ref("owner_names") }} as owner_names
left join {{ ref("display_names") }} as display_names
    on owner_names.owner_id = display_names.owner_id
