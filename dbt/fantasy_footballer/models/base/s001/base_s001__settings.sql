select
    year::int as year,
    reg_season_count::int as reg_season_count,
    matchup_periods as matchup_weeks,
    veto_votes_required::int as veto_votes_required,
    team_count::int as team_count,
    playoff_team_count::int as playoff_team_count,
    keeper_count::int as keeper_count,
    make_timestamp_ms(trade_deadline) as trade_deadline,
    division_map,
    name::varchar as name,
    tie_rule::varchar as tie_rule,
    playoff_tie_rule::varchar as playoff_tie_rule,
    playoff_matchup_period_length::int as playoff_matchup_period_length,
    playoff_seed_tie_rule::varchar as playoff_seed_tie_rule,
    scoring_type::varchar as scoring_type,
    faab::bool as faab,
    acquisition_budget::int as acquisition_budget,
    scoring_format
--    position_slot_counts
from {{ source("s001", "settings") }}
