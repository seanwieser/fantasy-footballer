with clutch_counts as (
    select
        team_id,
        team_year_id,
        year,
        count_if(is_clutch and outcome = 'W')::int as clutch_wins,
        count_if(is_clutch and outcome = 'L')::int as clutch_losses
    from {{ ref("int__team_week_results") }}
    where not is_playoff
    group by all
)

select
    team_id,
    team_year_id,
    year,
    clutch_wins::varchar || '-' || clutch_losses::varchar as record
from clutch_counts
