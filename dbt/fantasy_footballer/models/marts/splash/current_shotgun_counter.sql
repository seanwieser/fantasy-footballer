with shotgun_counter as (
    select
        owner_team_map.owner_name                                  as owner,
        owner_team_map.owner_id,
        shotgun_counts.shotgun_count                               as count,
        list_aggr(shotgun_counts.shotgun_weeks, 'string_agg', ', ') as weeks
    from {{ ref("int__team_shotgun_counts") }} as shotgun_counts
    left join {{ ref('int__owner_team_year_map') }} as owner_team_map
        on shotgun_counts.team_year_id = owner_team_map.team_year_id
    cross join {{ ref("int__current_season_year") }} as current_year
    where
        shotgun_counts.year = current_year.current_season_year and
        shotgun_counts.shotgun_count > 0
    order by
        count desc,
        weeks desc
)

select *
from shotgun_counter
