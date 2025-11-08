select
    src,
    src_table,
    meta__date_effective
from {{ ref("stg__source_metadata") }}
cross join {{ ref("int__current_season_year") }} current_year
where year = current_year.current_season_year