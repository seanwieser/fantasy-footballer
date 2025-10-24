with years as (
    select distinct year
    from {{ ref("owner_year_map") }}
),

weeks as (
    select unnest(generate_series(1, 18)) as week
),

year_week_combinations as (
    select
        years.year,
        weeks.week::integer as week,
        (years.year < 2021 and weeks.week >= 14) or
        (years.year >= 2021 and weeks.week >= 15) as is_playoff
    from years
    cross join weeks
)

select *
from year_week_combinations
order by year, week
