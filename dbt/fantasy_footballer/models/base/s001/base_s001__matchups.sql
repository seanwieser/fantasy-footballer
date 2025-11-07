with matchups_split as (
    select
        home_team::int as team_id,
        home_team::int || '_' || year::int as team_year_id,

        year::int as year,
        matchup_week::int as matchup_week,
        home_score::double as score_for,
        if(home_score::double = 0, 0, home_projected::double) as projected_score_for,
        home_lineup::varchar[] as matchup_lineup,
        is_playoff,
        matchup_type::varchar as matchup_type
    from {{ source("s001", "matchups") }}

    union all

    select
        away_team::int as team_id,
        away_team::int || '_' || year::int as team_year_id,

        year::int as year,
        matchup_week::int as matchup_week,
        away_score::double as score_for,
        if(away_score::double = 0, 0, away_projected::double) as projected_score_for,
        away_lineup::varchar[] as matchup_lineup,
        is_playoff,
        matchup_type::varchar as matchup_type
    from {{ source("s001", "matchups") }}
    where away_team is not null -- Opponent of bye matchup week is empty
)

select *
from matchups_split
