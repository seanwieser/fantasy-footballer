-- Validates that the bracket-reconstructed placements (is_champion/is_runner_up/is_third)
-- agree with ESPN's final_standing for the money places (1st, 2nd, 3rd). The toilet-bowl
-- places (11th, 12th) are intentionally NOT checked here: ESPN runs its own consolation
-- ladder over all bottom teams, which disagrees with the league's bottom-4 toilet bowl.
-- Any row returned is a mismatch and fails the test.
select
    team_year_id,
    reconstructed_place,
    final_standing
from {{ ref("int__team_postseason") }}
where
    (reconstructed_place in (1, 2, 3) and reconstructed_place is distinct from final_standing) or
    (final_standing in (1, 2, 3) and final_standing is distinct from reconstructed_place)
