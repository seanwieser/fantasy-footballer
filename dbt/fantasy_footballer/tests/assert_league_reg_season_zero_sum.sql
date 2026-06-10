-- Every regular-season game contributes exactly one win and one loss, and one team's points-for is its
-- opponent's points-against — so league-wide each season must net to zero on both. A nonzero diff means
-- the stg__team_weeks opponent self-join dropped or duplicated a side (the bug class behind most
-- head-to-head / scoring drift). Points are summed doubles, so compared at a 0.1 tolerance.
with by_year as (
    select
        year,
        count_if(outcome = 'W') as wins,
        count_if(outcome = 'L') as losses,
        sum(score_for) as points_for,
        sum(score_against) as points_against
    from {{ ref("int__team_week_results") }}
    where not is_playoff and outcome != 'U'
    group by year
)

select
    year,
    wins,
    losses,
    points_for,
    points_against
from by_year
where
    wins != losses or
    abs(points_for - points_against) > 0.1
