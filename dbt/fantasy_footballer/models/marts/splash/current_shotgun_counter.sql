with shotgun_counter as (
    select
        owner_team_map.owner_name                                                   as owner,
        count(*)::int                                                               as count,
        list_aggr(list_sort(array_agg(shotguns.week), 'ASC'), 'string_agg', ', ')   as weeks
    from {{ ref("int__shotguns") }}                 as shotguns
    left join {{ ref('int__owner_team_year_map') }} as owner_team_map
        on shotguns.team_year_id = owner_team_map.team_year_id
    cross join {{ ref("int__current_season_year") }} as current_year
    where
        shotguns.year = current_year.current_season_year and
        shotguns.is_shotgun
    group by
        owner_team_map.owner_name
    order by
        count desc,
        weeks desc
)

select *
from shotgun_counter
