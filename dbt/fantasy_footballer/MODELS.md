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

## Seeds (`main_seed_data`) — populated from B2 at boot, truncated in git

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
| `int__clutch_records` | team-season | Clutch W-L `record` string (regular-season games decided by `< 10` pts) + season points for/against. | `stg__team_weeks` (self-join), `int__matchup_week_playoff_map` |
| `int__shotguns` | team-week | `is_shotgun` = `score_for < 100` **or** the week's league-minimum score (regular season). | `stg__team_weeks`, `int__matchup_week_playoff_map` |
| `int__strength_of_schedule` | team-season (`team_year_id` unique) | Opponent-Wins (`ow`), Opponent's-Opponent-Wins (`oow`), composite `sos = ⅔·ow + ⅓·oow`; `*r` variants = remaining games. | `stg__team_weeks`, `base_s001__teams`, `base_s001__settings` |
| `int__source_freshness` | src_table (current season) | Current-season slice of `stg__source_metadata` for freshness display. | `stg__source_metadata`, `int__current_season_year` |
| `int__owner_season_scoring` | owner-season (`owner_year_id` unique) | Regular-season scoring per owner-season: `reg_points_total`, `reg_points_per_game`, `games_played`, `best_week_score`, `worst_week_score`, `made_playoffs`. Scoring workhorse for League Highlights. | `stg__team_weeks`, `int__matchup_week_playoff_map`, `int__owner_team_year_map`, `int__team_postseason` |
| `int__postseason_team_weeks` | team-week (postseason only, `team_week_id` unique) | Reconstructs bracket progression. Per postseason game: `bracket`, `matchup_type`, `is_championship_game`, `is_third_place_game`, `is_toilet_game`, and **`is_meaningful`** (does the game count toward metrics). See Postseason gotcha below. | `stg__team_weeks`, `base_s001__teams`, `base_s001__settings`, `stg__settings_matchup_weeks_map`, `base_s001__matchups` |
| `int__team_postseason` | team-season (`team_year_id` unique) | End-of-regular-season status + final placement: `bracket` ∈ {winners, toilet_bowl, kiss_my_sister}, `made_playoffs`, placement flags (`is_champion`, `is_runner_up`, `is_third`, `is_second_to_last`, `is_last`), `reconstructed_place`, plus ESPN `final_standing` (validated against the reconstruction for places 1-3). | `int__postseason_team_weeks`, `base_s001__teams` |

## Marts (`main_marts`) — page-specific final tables

Directory mirrors the frontend page that consumes it. Owner name attached, decimals rounded
for display.

| Mart | Frontend page | Purpose |
|---|---|---|
| `splash/current_standings` | `/` | Current-season standings table. |
| `splash/current_shotgun_counter` | `/` | Current-season shotgun tally per owner. |
| `owners/home/owners_by_year` | `/owner_history` | Owner dropdown options grouped by year. |
| `owners/spotlight/season_overview` | `/owner_history/{owner}/{year}` | Season summary card for an owner. |
| `owners/spotlight/season_schedule` | `/owner_history/{owner}/{year}` | That owner's weekly schedule + results. |
| `stats_center/player_data/player_data_table` | `/stats_center` player data | Aggregated player scoring table. |
| `stats_center/strength_of_schedule/strength_of_schedule` | `/stats_center` SOS | SOS leaderboard. |
| `stats_center/draft_analysis/snake_draft_table` | `/stats_center` draft | Snake-draft board. |
| `stats_center/draft_analysis/auction_draft_table` | `/stats_center` draft | Auction-draft board. |
| `stats_center/league_highlights/all_time_records` *(in progress)* | `/stats_center` league highlights | All-time best/worst/extreme records (tidy/long). See `docs/39-league-highlights-page.md`. |
| `stats_center/league_highlights/season_highlights` *(planned)* | `/stats_center` league highlights | Per-season title holders + leaderboards. |

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
