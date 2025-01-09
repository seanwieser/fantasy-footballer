with shotgun_counter as (
    select
        shotguns.owner_name                                                         as "Owner",
        count(*)                                                                    as "Count",
        list_aggr(list_sort(array_agg(shotguns.week), 'ASC'), 'string_agg', ', ')   as "Weeks"
    from {{ ref("int_shotguns_by_owner_year_week") }}   as shotguns
    cross join {{ ref("current_year") }}                as current_year
    where
        shotguns.year = current_year.this
    group by shotguns.owner_name
    order by "Count" desc
)

select *
from shotgun_counter
