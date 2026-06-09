select
    owner_id,
    year,
    record,
    acquisitions,
    budget,
    standing,
    trades,
    streak,
    clutch_record,
    shotguns,
    points_for,
    points_for_per_week,
    points_against,
    points_against_per_week
from {{ ref("int__team_season_summary") }}
