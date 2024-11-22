select
    standing                 as "Standing",
    team_name                as "Name",
    owner_name               as "Owner",
    wins                     as "Wins",
    losses                   as "Losses",
    round(points_for, 2)     as "Points For",
    round(points_against, 2) as "Points Against",
    streak                   as "Streak"
from {{ ref("stg_s001__teams") }}
where year = '{{ modules.datetime.datetime.now().year }}'
order by standing
