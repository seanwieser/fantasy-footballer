select
    source_metadata.src,
    source_metadata.src_table,
    source_metadata.meta__date_effective
from {{ ref("stg__source_metadata") }} as source_metadata
cross join {{ ref("int__current_season_year") }} as current_year
where source_metadata.year = current_year.current_season_year
