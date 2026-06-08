# dbt data-model map

A human- and agent-readable map of every model in this dbt project: each model's
**grain**, **purpose**, **key columns**, and **upstream** refs. Use it to understand the
warehouse without re-reading every `.sql` file.

> **Maintenance:** this file is a living map. **If you add, remove, or materially change a
> model (grain, purpose, key columns, or its upstream refs), update the corresponding entry
> here in the same change.** Per-column type/description detail lives in each directory's
> `properties.yml` (contract-enforced) — don't duplicate it here; this file is the
> cross-model overview that `properties.yml` can't express.

To inspect any model's actual data, use the read-only helper (see root `CLAUDE.md`):
`make query SQL="select * from main_intermediate.int__owner_season_scoring limit 10"`.

---

## Conventions you need to read this map

- **Schemas (DuckDB catalog `main`):** `main_base`, `main_staging`, `main_intermediate`,
  `main_marts`, `main_seed_data`.
- **Composite IDs** are the standard join keys, built with `||`:
  | ID | Format | Grain it identifies |
  |---|---|---|
  | `team_year_id` | `team_id_year` | a team in a season |
  | `team_week_id` | `team_id_year_week` | a team in one week |
  | `owner_year_id` | `owner_id_year` | an owner in a season |
  | `player_year_id` | `playerid_year` | a player in a season |
  | `player_week_id` | `playerid_year_week` | a player in one week |
- **`outcome` codes** (on weekly grains): `W` win, `L` loss, `T` tie, `U` unplayed/future.
  Almost every "played games" filter is `outcome != 'U'`.
- **`meta__source_path` / `meta__date_effective` / `meta__date_pulled`** ride through every
  `base_*` model unchanged; they power `stg__source_metadata` → `int__source_freshness`.
- **Owner identity** (`owner_name`) is *not* in the source — it's attached by joining
  `int__owner_team_year_map` (the bridge from ESPN `display_name` → seed `owner_id`).

## Lineage at a glance

```
s001 sources ─► base_s001__*  ─►  staging (stg__*)  ─►  intermediate (int__*)  ─►  marts/<page>
seeds (owner_names,            (unnest arrays,        (reusable computations)     (page-specific,
 display_names, users)          flatten to weekly                                  owner_name attached,
                                grain)                                             rounded for display)
```

---

## Base layer (`main_base`) — 1:1 with sources, cast + rename only

| Model | Grain | Purpose & key columns | Upstream |
|---|---|---|---|
| `base_s001__teams` | team-season (`team_year_id`) | Season team record (`wins/losses/ties`, `points_for/against`, `standing`, `final_standing`, `streak`, `playoff_pct`). Holds **`weeks_raw`** — a struct array of per-week `{week, lineup, score_for, outcome, opponent_team_id}` that staging unnests. Derives `display_name` from `owners[1]` first/last name (the link to owner identity). | `source(s001, teams)` |
| `base_s001__matchups` | team-matchup_week (home+away unioned) | One row per team per matchup. `score_for`, `projected_score_for`, `matchup_lineup`, `is_playoff`, **`matchup_type`**. Used for playoff classification + matchup lineups. | `source(s001, matchups)` |
| `base_s001__players` | player-season (`player_year_id`) | Player meta (`position_slot`, `is_flex`, `nfl_team`, ranks, ownership). Holds **`stats_raw`** — weekly stats array that `stg__player_weeks` unnests. | `source(s001, players)` |
| `base_s001__settings` | season (`year`) | League config: `reg_season_count`, `playoff_team_count`, `team_count`, **`matchup_weeks`** (matchup_period→weeks map), `scoring_format`, tie rules. | `source(s001, settings)` |
| `base_s001__draftpicks` | pick (`team_year_id` + `player_year_id`) | Draft results: `round_num`, `round_pick`, `bid_amount`, `keeper_status`, `is_auction` (= `nominating_team_id is not null`), `nominating_team_year_id`. | `source(s001, draftpicks)` |

## Seeds (`main_seed_data`) — populated from B2 at boot, git-ignored

| Seed | Grain | Purpose |
|---|---|---|
| `owner_names` | `owner_id` | Canonical owner identity (`owner_id` → `owner_name`). |
| `display_names` | `owner_id` | ESPN `display_name` (first+last) → `owner_id`. Bridges source names to identity. |
| `users` | username | Auth (login hashes). Not part of analytics lineage. |

## Staging (`main_staging`) — unnest arrays, flatten to weekly grain

| Model | Grain | Purpose & key columns | Upstream |
|---|---|---|---|
| `stg__team_weeks` | **team-week** (`team_week_id`) | **The weekly workhorse.** Unnests `teams.weeks_raw` to one row per team per week: `score_for`, `outcome`, `lineup`, and opponent keys (`opponent_team_week_id` for self-joins). Self-join by role (`team_weeks` + `opponent_weeks`) for head-to-head. | `base_s001__teams` |
| `stg__team_week_players` | team-week-player (`player_week_id` + `lineup_slot`) | Unnests `stg__team_weeks.lineup` → each rostered player's slot per week (played weeks only). `RB/WR/TE` slot normalized to `FLEX`. | `stg__team_weeks` |
| `stg__player_weeks` | player-week (`player_week_id`) | Unnests `players.stats_raw` → weekly player box score (`points`, passing/rushing/receiving/kicking stat lines, `team_win`). | `base_s001__players` |
| `stg__matchup_players` | matchup-week-player | Unnests `matchups.matchup_lineup` (`score_for > 0`, i.e. real weeks). Carries `is_playoff`, `matchup_type`. | `base_s001__matchups` |
| `stg__owner_display_names` | `display_name` | Joins `owner_names` + `display_names` seeds → `owner_id` / `owner_name` / `display_name` bridge. | seeds |
| `stg__settings_matchup_weeks_map` | year-matchup_week-week | Unnest + unpivot `settings.matchup_weeks` → maps a matchup_week to its calendar week(s). | `base_s001__settings` |
| `stg__source_metadata` | src_table-year | Unions `meta__*` columns across base models for freshness tracking. | base models |

## Intermediate (`main_intermediate`) — reusable computations

| Model | Grain | Purpose & key columns | Upstream |
|---|---|---|---|
| `int__owner_team_year_map` | team-season (`team_year_id` unique) | **The owner-identity bridge.** Maps `owner_id`/`owner_name`/`owner_year_id` ↔ `team_id`/`team_year_id`/`team_name`/`year` (via `display_name`). Joined by nearly every mart to surface `owner_name`. | `base_s001__teams`, `stg__owner_display_names` |
| `int__owner_team_map` | owner-team | Dedup owner↔team across seasons (franchise ownership history, year-agnostic). | `int__owner_team_year_map` |
| `int__current_season_year` | single row | `max(year)` as `current_season_year`. Cross-join into any mart that should auto-update each season. **Never hard-code the year.** | `int__owner_team_year_map` |
| `int__matchup_week_playoff_map` | year-week | `is_playoff` flag per calendar week. | `stg__settings_matchup_weeks_map`, `base_s001__matchups` |
| `int__weeks_played_by_year` | year | Min regular-season weeks played that season. | `stg__team_weeks`, `int__matchup_week_playoff_map` |
| `int__clutch_records` | team-season (`team_year_id` unique) | Clutch W-L `record` string (regular-season games decided by `< 10` pts), derived from the `is_clutch` flag. Season points for/against moved to `int__owner_season_scoring`. | `int__team_week_results` |
| `int__shotguns` | team-week | `is_shotgun` = `score_for < 100` **or** the week's league-minimum score (regular season). | `stg__team_weeks`, `int__matchup_week_playoff_map` |
| `int__strength_of_schedule` | team-season (`team_year_id` unique) | Opponent-Wins (`ow`), Opponent's-Opponent-Wins (`oow`), composite `sos = ⅔·ow + ⅓·oow`; `*r` variants = remaining games. | `stg__team_weeks`, `base_s001__teams`, `base_s001__settings` |
| `int__source_freshness` | src_table (current season) | Current-season slice of `stg__source_metadata` for freshness display. | `stg__source_metadata`, `int__current_season_year` |
| `int__owner_season_scoring` | owner-season (`owner_year_id` unique) | **The canonical season-scoring model** (points for AND against): `reg_points_total`, `reg_points_against`, `reg_points_per_game`, `games_played`, `best_week_score`, `worst_week_score`, `made_playoffs`. Non-clutch marts read season points from here. | `int__team_week_results`, `int__owner_team_year_map`, `int__team_postseason` |
| `int__postseason_team_weeks` | team-week (postseason only, `team_week_id` unique) | Reconstructs bracket progression. Per postseason game: `bracket`, `matchup_type`, `is_championship_game`, `is_third_place_game`, `is_toilet_game`, and **`is_meaningful`** (does the game count toward metrics). See Postseason gotcha below. | `stg__team_weeks`, `base_s001__teams`, `base_s001__settings`, `stg__settings_matchup_weeks_map`, `base_s001__matchups` |
| `int__team_postseason` | team-season (`team_year_id` unique) | End-of-regular-season status + final placement: `bracket` ∈ {winners, toilet_bowl, kiss_my_sister}, `made_playoffs`, placement flags (`is_champion`, `is_runner_up`, `is_third`, `is_second_to_last`, `is_last`), `reconstructed_place`, plus ESPN `final_standing` (validated against the reconstruction for places 1-3). | `int__postseason_team_weeks`, `base_s001__teams` |
| `int__matchup_margins` | regular-season game (`team_week_id` unique) | One row per head-to-head game: `winner_team_year_id`, `loser_team_year_id`, scores, `margin`, `is_tie`. Feeds tightest-matchups / biggest-blowouts. | `stg__team_weeks`, `int__matchup_week_playoff_map` |
| `int__lucky_records` | owner-week (regular season, `team_week_id` unique) | Median-based luck (definition per the alexcates.com "better to be lucky than good" article): `is_lucky_win` (won below week median), `is_unlucky_loss` (lost above it), and experimental `luck_points` (teams above on a win / below on a loss). | `stg__team_weeks`, `int__matchup_week_playoff_map` |
| `int__season_titles` | owner-season (`owner_year_id` unique) | Title roll-up: amount columns + a boolean flag per season title (scoring/non-scoring, matchup, snub, playoff luck-in, clutch win/lose, lucky/unlucky, shotgun, no-shotgun). Co-title semantics (rank()=1). **Snub/luck-in are gated:** a self-join (`points_vs_field`) counts `playoff_teams_outscored` / `nonplayoff_teams_outscoring`, and snub requires outscoring ≥1 playoff team (luck-in the mirror) — so clean-cutoff years award neither. Those counts also size the season-card subtitle ("outscored 3 who made it"). Beyond the single-title flags, `is_snubbed` / `is_lucked_in` mark **every** snubbed/lucked-in team-season (the occurrence, not just the worst) — feeding the all-time career-total + biggest-snub leaderboards. | `int__owner_season_scoring`, `int__clutch_records`, `int__shotguns`, `int__lucky_records` |
| `int__season_titles_long` | owner-season × title metric | **Tidy/unpivoted `int__season_titles`** — the single place the title → `amount` → `is_title_holder` mapping is defined. Every owner-season fans out to one row per title metric. Consumed by `season_highlights` (holders) and `int__owner_career_summary` (counts/sums). | `int__season_titles` |
| `int__owner_career_summary` | owner (`owner_id` unique) | Career roll-ups per owner: tennis-style title counts, cumulative lucky/unlucky/shotgun + clutch W-L totals, `seasons_played` (tenure), `snub_total`/`luck_in_total` (career snubbed/lucked-in seasons), `points_total`/`games_total`/`points_per_game`/`clutch_win_pct`. Keeps `all_time_records` a thin select. | `int__season_titles_long`, `int__owner_season_scoring`, `int__season_titles` |
| `int__team_shotgun_counts` | team-season (`team_year_id` unique) | Regular-season `shotgun_count` + sorted `shotgun_weeks` list per team-season (count 0 if none). Centralizes the tally summed inline by `current_shotgun_counter` + `season_overview`. | `int__shotguns` |
| `int__player_season_stats` | player-season (`player_year_id` unique) | Per player-season `total_points` + `num_weeks` (week 0 excluded) plus position/flex/rank/team. Backs `player_data_table`. | `stg__player_weeks` |
| `int__team_week_results` | team-week (`team_week_id` unique) | Team's-perspective weekly result with opponent resolved: `opponent_team_name`/`opponent_owner_name`, `score_for`/`score_against`, `outcome`, `margin`, `is_clutch`, `is_shotgun`, `is_playoff`. Backs `season_schedule`. | `stg__team_weeks` (self-join), `int__owner_team_year_map`, `int__matchup_week_playoff_map`, `int__shotguns` |
| `int__team_week_highlights` | team-week (regular season, `team_week_id` unique) | A boolean per **week-grain** league highlight: `is_shotgun`, `is_lucky_win`/`is_unlucky_loss`, `is_clutch_win`/`is_clutch_loss`, `is_best_week`/`is_worst_week` (held the league single highest/lowest score that season → aligns with `matchup_title`/`bad_matchup_title`), `is_tightest_game`/`is_biggest_blowout` (won the season's single smallest/largest margin → aligns with `tightest_matchups`/`biggest_blowouts`). Each flag is the week-level occurrence of a season highlight; computes the league extremes once so marts stay thin. Backs `season_schedule`; intended source for a future activity/notification feed (FF-010). | `int__team_week_results`, `int__lucky_records` |
| `int__team_season_summary` | team-season (`team_year_id` unique) | Owner-spotlight card: record, acquisitions, FAAB budget, standing, trades, streak, clutch record, shotguns, regular-season points for/against + per-week. Owner is the actual per-season owner; points for/against from `int__owner_season_scoring`, clutch record from `int__clutch_records`. Backs `season_overview`. | `base_s001__teams`, `int__owner_season_scoring`, `int__clutch_records`, `int__owner_team_year_map`, `int__weeks_played_by_year`, `int__team_shotgun_counts` |

## Marts (`main_marts`) — page-specific final tables

Directory mirrors the frontend page that consumes it. Owner name attached, decimals rounded
for display.

| Mart | Frontend page | Purpose |
|---|---|---|
| `splash/current_standings` | `/` | Current-season standings table. |
| `splash/current_shotgun_counter` | `/` | Current-season shotgun tally per owner. |
| `owners/home/owners_by_year` | `/owner_history` | Owner dropdown options grouped by year. |
| `owners/spotlight/season_overview` | `/owner_history/{owner}/{year}` | Season summary card for an owner. |
| `owners/spotlight/season_schedule` | `/owner_history/{owner}/{year}` | **Thin** mart: one row per owner-week (reg season) = display columns (opponent, scores, `outcome`) joined to the boolean week-grain highlight flags from **`int__team_week_highlights`** (all the "what happened" logic lives there). Frontend renders the flags as section-colored chips. Upstream: `int__team_week_results`, `int__team_week_highlights`. |
| `stats_center/player_data/player_data_table` | `/stats_center` player data | Aggregated player scoring table. |
| `stats_center/strength_of_schedule/strength_of_schedule` | `/stats_center` SOS | SOS leaderboard. |
| `stats_center/draft_analysis/snake_draft_table` | `/stats_center` draft | Snake-draft board. |
| `stats_center/draft_analysis/auction_draft_table` | `/stats_center` draft | Auction-draft board. |
| `stats_center/league_highlights/all_time_records` | `/stats_center` league highlights | One row per metric x ranked owner (tidy/long): tennis-style title counts, career totals, single-extreme records. Counts/totals read `int__owner_career_summary`; records read the season/week/game intermediates. Metric metadata (key→section/category/label/sort_sign/result_n/value_format/**description**/**subtitle_kind**/**display_order**) comes from the **`all_time_record_metrics` seed**; both leaderboards and records keep top 3 (`result_n`). `description` = tooltip text; `subtitle_kind` drives the card subtitle — `years` (season-award counts surface **`years_won`**, a chrono `string_agg` of title years from `int__season_titles_long` — and for `snub_total_count` / `luck_in_total_count`, the snub/lucky-in years from `int__season_titles`), `tenure` (career accumulations → UI shows seasons-played), `context` (single records → year/week/opponent detail); `display_order` = reading order within a section (single week → season → career → titles), drives card + sub-cluster order in the UI; `detail` = secondary line behind the value (clutch W-L record for clutch-% rows, losing owner + winner-loser score for margin records, the English label + points-for tiebreak for `biggest_snub`/`biggest_luck_in`, e.g. "playoff teams outscored · 1867 PF"). The Playoff category carries the full snub/lucky-in family: title (tennis), `*_total_count` (career occurrences via `is_snubbed`/`is_lucked_in`), `biggest_snub`/`biggest_luck_in` (record ranked by teams out/under-scored), plus the existing points records. **`metric_type` taxonomy** (when adding a seed row): `record` = the single most-extreme value ever, one holder; `count` = tennis-style tally of *how many seasons* an owner held a title (magnitude within a season is irrelevant — winning by 0.1 or 400 both count as 1); `total` = a continuous career sum, where "most …" and "least …" are the same metric sorted desc vs asc. |
| `stats_center/league_highlights/season_highlights` | `/stats_center` league highlights | One row per `year` x `metric_key` x `rank`. Title holders (co-titles included) read straight from `int__season_titles_long where is_title_holder`; margin leaderboards (tightest/blowouts) from `int__matchup_margins`, keeping season top 3 with the full `detail` subtitle composed in the mart (`def. {opponent} · {score} · Wk N`), so the frontend renders it as-is. Metric metadata + `description` (tooltip) + **`section`** (Scoring/Matchups/Shotgun/Clutch grouping) + **`display_order`** (intra-section card order) come from the **`season_highlight_metrics` seed**; the frontend clusters title cards by `section` mirroring the All-Time tab. Each title row also gets a **`detail` subtitle** describing how/when/where it was earned — end-of-reg-season seed (`standing`, e.g. "7th seed") for scoring/bottom-scorer/snub/lucky-in, the key week(s) (from `int__shotguns`/`int__lucky_records`/`int__team_week_results`) for week/shotgun/lucky/unlucky titles — and clutch titles headline the W-L `record` (`int__clutch_records`) as their `display_value`. The seed also carries `empty_label` (e.g. "Everyone shotgunned this season"); the frontend reads the catalog directly so a title with no holder in a year still shows a placeholder card. |
| `utilities/current_year` | frontend `utils.py` | Single row, latest season `year` (dropdown default). Wraps `int__current_season_year`. |
| `utilities/owner_year_map` | frontend `utils.py` | One row per owner-season (`owner_id`, `owner_name`, `year`) for owner/year dropdowns. Wraps `int__owner_team_year_map`. |
| `utilities/owners` | frontend (league highlights) | **Owner dimension** — one row per `owner_id`: `owner_name`, `first_year`, `last_year`, `seasons_played` (tenure), `is_active` (true = fielded a team in the current season; false = retired). Wraps `int__owner_team_year_map` × `int__current_season_year`. |
| `utilities/nfl_teams` | frontend `utils.py` | Distinct `nfl_team` list (incl. `'None'` sentinel) for the NFL-team filter. Wraps `base_s001__players`. |

---

## Gotchas / non-obvious data facts

- **`is_playoff` includes consolation games.** In `base_s001__matchups`, `is_playoff` is true
  for `WINNERS_BRACKET`, `WINNERS_CONSOLATION_LADDER`, **and** `LOSERS_CONSOLATION_LADDER` —
  so every team "appears in a playoff matchup." It really means "is a postseason week" (used
  for the regular-season filter `not is_playoff` in `int__matchup_week_playoff_map`). For
  bracket/placement logic, use `int__team_postseason` / `int__postseason_team_weeks` instead.
- **2018 is special-cased upstream** in the source `MatchupTransformer` (uses `scoreboard`
  instead of `box_scores`). Season length also differs: 13 regular-season games in 2018–2019
  vs 14 from 2021 on — relevant whenever comparing season totals across years (prefer
  per-game where fairness matters).
- **Within a season every owner plays the same number of regular-season games**, so total
  points and points-per-game produce identical *within-season* rankings; they only diverge
  *across* seasons (the 13- vs 14-game difference).
- **`weeks_raw` (teams) vs `matchup_lineup` (matchups)** are two different lineup sources;
  `stg__team_weeks` flattens the former, `stg__matchup_players` the latter.
- **`away_team` can be null** in `base_s001__matchups` (bye week opponent) — the home/away
  union filters `away_team is not null`.
- **Everything is `materialized: table` with `contract: enforced`.** A new/renamed column
  fails the build unless its `data_type` is declared in the sibling `properties.yml`.

### Postseason / bracket rules (read before touching `int__*postseason*`)

Regular season and postseason are **separate concepts** — game counts per team are *not*
consistent in the postseason because they depend on outcomes. All current regular-season
metrics exclude the postseason entirely (`not is_playoff`). Postseason logic lives in
`int__postseason_team_weeks` (team-week) and `int__team_postseason` (team-season).

At the end of the regular season each team is in one of three brackets:

- **Winners bracket** (championship) — `playoff_team_count` teams (4 pre-2020, 6 since).
  Single elimination. **Determined by actual `WINNERS_BRACKET` participation, not seed**
  (in 2018 the league ran two divisions — East/West, since removed — so `standing` is
  division-aware and ≠ playoff seed: the winners bracket is standings 1,3,4,5 because a 7-6
  West division winner was seeded 2nd). 1st = wins the final, 2nd = loses it, 3rd = wins the
  game between the two semifinal losers.
- **Toilet bowl** — the **bottom 4 seeds** (`standing > team_count - 4`), 2 weeks. Round 1:
  the two winners **escape** (a win is good). Round 2: the two round-1 losers play — that
  loser is **last (12th)**, the winner is **2nd-to-last (11th)**. The two escapees' round-2
  games are meaningless (they play middle teams).
- **Kiss my sister** (middle) — everyone else. **Every one of their games is meaningless.**

`is_meaningful` (in `int__postseason_team_weeks`) is the flag that protects metrics: true only
for winners-bracket games while alive, the 3rd-place game, and real toilet-bowl games.
Everything else (eliminated-team placement ladders, escapee filler, all middle games) is false.

Format quirks to respect:
- **2-week format (2018-19)** labels the 3rd-place game `WINNERS_BRACKET` (no consolation
  ladder); the **3-week format (2020+)** drops eliminated teams to `WINNERS_CONSOLATION_LADDER`.
  So championship/3rd-place games are identified by **semifinal result** (second-to-last
  postseason week), not by the final week's `matchup_type`.
- **ESPN `final_standing` is reliable for 1st/2nd/3rd** (validated by
  `tests/assert_postseason_placements_match_espn.sql`) but **wrong for the toilet bowl** — it
  runs its own consolation ladder over all bottom teams, so the league's bottom-4 toilet
  outcome is reconstructed from bracket progression instead.
