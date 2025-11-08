select distinct
    's001' as src,
    'matchups' as src_table,
    year,
    meta__source_path,
    meta__date_effective,
    meta__date_pulled
from {{ ref("base_s001__matchups") }}
union all
select distinct
    's001' as src,
    'players' as src_table,
    year,
    meta__source_path,
    meta__date_effective,
    meta__date_pulled
from {{ ref("base_s001__players") }}
union all
select distinct
    's001' as src,
    'settings' as src_table,
    year,
    meta__source_path,
    meta__date_effective,
    meta__date_pulled
from {{ ref("base_s001__settings") }}
union all
select distinct
    's001' as src,
    'teams' as src_table,
    year,
    meta__source_path,
    meta__date_effective,
    meta__date_pulled
from {{ ref("base_s001__teams") }}