# 39 — League Highlights Page

A new dashboard page under **Stats Center** that surfaces the *best / worst / most
extreme* metrics across every kind of data the league has. The spirit is celebratory
and roast-y: "who has the most scoring titles," "what's the single biggest blowout
ever," "who keeps lucking into the playoffs."

We build this **bottom-up**:

1. **dbt** — model the analytics upstream→downstream (`intermediate/` → `marts/`) so the
   frontend only issues thin `SELECT`s. This doc is mostly about getting these
   definitions exactly right.
2. **Frontend** — a NiceGUI page that renders the precomputed marts in a fun, engaging
   way (leaderboards, record cards, a season picker).

---

## 1. Shared vocabulary

The brain-dump uses a consistent naming grammar. These suffixes are **load-bearing** —
they tell you the metric's type and time window.

| Suffix / word | Type | Meaning |
|---|---|---|
| `... count` | **discrete** | An integer count. Either a tennis-style title tally (seasons won) or a cumulative event count (e.g. total shotguns). |
| `... total` | **continuous** | A summed quantity across all seasons (e.g. career points). Continuous values. |
| `... amount` / `... record` | **single extreme** | One record-holding value — the single most extreme season/game ever (e.g. highest-scoring season). |
| `... title` | **per-season award** | Exactly one winner per season for that metric. The atomic unit that tennis-style counts aggregate. |

### Tennis-style aggregation

Many **all-time `count`** metrics are scored "like tennis": each **season** produces one
**title** winner, and the all-time count is *how many seasons* an owner held that title.
The magnitude of the win within a season is irrelevant to the count — winning the scoring
title by 0.1 or by 400 both count as exactly **1**.

> Example: "scoring title count" = the number of seasons in which an owner finished #1 in
> regular-season points. The best single-season points value that *won* a title is tracked
> separately as the "highest scoring season amount" (a record, not a count).

### Three flavors of all-time metric

1. **Title counts** (tennis-style) — `count` of seasons an owner held a title.
2. **Continuous totals** — cumulative sum/career value across all seasons (`total`).
   Note: "most ... total" and "least ... total" are the **same underlying metric**, just a
   leaderboard sorted descending vs. ascending.
3. **Single-season / single-game records** (`amount` / `record`) — the one most extreme
   value across all of league history, with the owner + season/week that holds it.

---

## 2. Confirmed design decisions (this session)

| # | Question | Decision |
|---|---|---|
| 1 | What grain is the "matchup" sub-window? | **Single best/worst week.** "Matchup title" = the highest single-week score in a season; "bad matchup title" = the lowest single-week score in a season. Records = highest / lowest single-week score ever. |
| 2 | What do "non-playoff scoring title" / "playoff non-scoring title" mean? | **Snub / undeserving narrative.** *non-playoff scoring title* = the **highest-scoring team that MISSED the playoffs** (robbed). *playoff non-scoring title* = the **lowest-scoring team that MADE the playoffs** (lucked in). |
| 3 | How are season point totals scoped? | **Regular-season weeks only.** Surface **both** the raw **total** and **points-per-game** so we can compare the two before deciding which to ship. (Per-game normalizes uneven season lengths / 2018 special-casing.) |
| 4 | How is a "lucky win" / "unlucky loss" defined? | **Median-based** (per the [alexcates.com article](https://www.alexcates.com/post/better-to-be-lucky-than-good-is-it-really-for-fantasy-football)). A **lucky win** = you won but scored **below that week's league median** (you'd have lost to most teams). An **unlucky loss** = you lost but scored **above the median**. Magnitude via **luck points**: on a win, `luck_points` = # of teams that outscored you that week; on a loss, the negative of # of teams you outscored. Season luck = sum of luck points over regular-season games. |

### Scoping rules that fall out of the above

- **Regular season only**: every scoring/title computation filters to
  `not is_playoff` via `int__matchup_week_playoff_map`, except the **playoff snub** metrics
  which need playoff participation to classify teams. Points compared across owners are
  always regular-season points so everyone is on the same slate.
- **Variable season length / 2018**: because we compute **points-per-game** alongside
  totals, uneven game counts are handled. `games_played` per owner-season comes from
  counting `outcome != 'U'` regular-season weeks (mirrors `int__strength_of_schedule`).
- **Clutch** = regular-season games decided by `< 10` points (already in
  `int__clutch_records`).
- **Shotgun** = a week where `score_for < 100` OR `score_for` is the week's league minimum
  (already in `int__shotguns`, regular season only).

---

## 3. Metric catalog

Two top-level sections mirror the brain-dump: **All-time** and **Season** (the latter
shows the title holders + amounts for a single selected season).

Legend for **Type**: `T-count` = tennis-style title count · `E-count` = cumulative event
count · `total` = continuous career sum · `record` = single extreme value.

### 3.1 All-time

#### Scoring → Season (regular-season points)

| Metric | Type | Definition |
|---|---|---|
| scoring title count | T-count | # seasons with the **most** regular-season points (winner per season). |
| most points scored total | total | Career cumulative regular-season points (leaderboard, desc). |
| highest scoring season amount | record | The single **highest** regular-season points total ever (best scoring title). |
| non-scoring title count | T-count | # seasons with the **least** regular-season points (scoring wooden spoon). |
| least points scored total | total | Same career-points metric, leaderboard asc (fewest). |
| lowest scoring season amount | record | The single **lowest** regular-season points total ever (worst non-scoring title). |

> Each of the above is computed twice — once on **total points**, once on
> **points-per-game** — and surfaced side by side for the product decision.

#### Scoring → Matchup (single week)

| Metric | Type | Definition |
|---|---|---|
| matchup title count | T-count | # seasons in which the owner posted that season's **highest single-week** score. |
| best matchup title amount | record | Highest single-week score ever recorded. |
| bad matchup title count | T-count | # seasons in which the owner posted that season's **lowest single-week** score. |
| worst matchup title amount | record | Lowest single-week score ever recorded. |

#### Scoring → Playoff (snub / undeserving)

| Metric | Type | Definition |
|---|---|---|
| non-playoff scoring title count | T-count | # seasons the owner was the **highest scorer to MISS** the playoffs. |
| best non-playoff scoring title amount | record | Highest regular-season points among teams that **missed** playoffs, ever. |
| playoff non-scoring title count | T-count | # seasons the owner was the **lowest scorer to MAKE** the playoffs. |
| worst playoff non-scoring title amount | record | Lowest regular-season points among teams that **made** playoffs, ever. |

> Requires a "made the playoffs" flag per team-season — derive from playoff matchup
> participation (`is_playoff` rows in `base_s001__matchups`) and/or `playoff_team_count`
> from `base_s001__settings`. See Open Questions.

#### Clutch (games decided by `< 10`, regular season — from `int__clutch_records`)

| Metric | Type | Definition |
|---|---|---|
| clutch winning title count | T-count | # seasons with the **best** clutch record. |
| best clutch record total percentage | total | Career clutch win % (aggregate clutch W / clutch games across all seasons). |
| clutchest season record | record | The single **best** season clutch record ever (ranked by clutch **win count**, tiebroken by win %; see §6.4). |
| clutch losing title count | T-count | # seasons with the **worst** clutch record. |
| worst clutch record total percentage | total | Career clutch win %, leaderboard asc (lowest). |
| un-clutchest season record | record | The single **worst** season clutch record ever (ranked by clutch **loss count**, tiebroken by win %; see §6.4). |

#### Matchups — luck & margins

| Metric | Type | Definition |
|---|---|---|
| lucky winner title count | T-count | # seasons with the **most lucky wins** (win while below week's median). |
| lucky wins total count | E-count | Career cumulative # of lucky wins. |
| luckiest win amount record | record | The single **luckiest** win ever (highest `luck_points` — won with the lowest weekly rank). |
| un-lucky loser title count | T-count | # seasons with the **most unlucky losses** (loss while above week's median). |
| un-lucky losses total count | E-count | Career cumulative # of unlucky losses. |
| un-luckiest loss amount record | record | The single **unluckiest** loss ever (most-negative `luck_points` — lost with the highest weekly rank). |
| tightest matchups | record (top-N) | Smallest victory margins ever (leaderboard of closest games). |
| biggest blowouts | record (top-N) | Largest victory margins ever (leaderboard of routs). |

#### Shotgun (from `int__shotguns`)

| Metric | Type | Definition |
|---|---|---|
| shotgun title count | T-count | # seasons with the **most** shotguns. |
| most shotgun total count | E-count | Career cumulative # of shotguns (desc). |
| highest shotgun season record | record | Most shotguns in a single season ever. |
| most no-shotgun seasons | E-count | # of an owner's seasons with **zero** shotguns. |
| least shotgun total count | E-count | Career cumulative # of shotguns (asc, fewest). |

### 3.2 Season view (showing amounts)

For a **selected season**, show the holder + amount for each title. (Brain-dump kept some
`count` suffixes here; interpreted as a note-taking artifact — the season view always shows
*who held the title that season and the value*. Flagged in Open Questions.)

- **Scoring → Season**: scoring title · non-scoring title · (both via total & PPG)
- **Scoring → Matchup**: matchup title (best week) · bad matchup title (worst week)
- **Scoring → Playoff**: non-playoff scoring title (top snub) · playoff non-scoring title (top luck-in)
- **Clutch**: clutch winning title · clutch losing title
- **Matchups**: lucky winner title · unlucky loser title · tightest matchups · biggest blowouts (within season)
- **Shotgun**: shotgun title · no-shotgun season(s)

---

## 4. Proposed dbt architecture

Built bottom-up (`intermediate/` → `marts/`).

**Existing models we reuse as-is:**

- `int__clutch_records` — per owner-season clutch W-L (games decided by `< 10`).
- `int__shotguns` — per owner-week `is_shotgun` flag.
- `int__matchup_week_playoff_map` — `is_playoff` flag per week.
- `int__owner_team_year_map` — owner identity for a team-season.
- `int__current_season_year` — single-row "current" year for default selections.

### New intermediate models

Each bullet is one new model: **name** — grain, then the columns / what it feeds.

- **`int__postseason_team_weeks`** — postseason bracket progression. ✅ *Built.*
  - Grain: one row per team-week (postseason weeks only).
  - Columns: `bracket`, `matchup_type`, `is_championship_game`, `is_third_place_game`,
    `is_toilet_game`, `is_meaningful` (protects metrics from dead/kiss-my-sister games).
  - Feeds: `int__team_postseason`; any future postseason-based highlight.
  - See MODELS.md → "Postseason / bracket rules" for the full league-specific logic.

- **`int__team_postseason`** — team-season postseason status + placement. ✅ *Built.*
  - Grain: one row per team-season (`team_year_id`).
  - Columns: `bracket` ∈ {winners, toilet_bowl, kiss_my_sister}, `made_playoffs`, placement
    flags (`is_champion`, `is_runner_up`, `is_third`, `is_second_to_last`, `is_last`),
    `reconstructed_place`, `final_standing`.
  - A singular dbt test asserts the bracket reconstruction matches ESPN `final_standing` for
    places 1-3 (toilet bowl is reconstructed; ESPN disagrees there).
  - Feeds: `made_playoffs` for the playoff-snub metrics; champion/placement highlights.

- **`int__owner_season_scoring`** — the scoring workhorse. ✅ *Built.*
  - Grain: one row per owner-season.
  - Columns: `owner_id`, `owner_name`, `owner_year_id`, `year`, `reg_points_total`,
    `reg_points_per_game`, `games_played`, `best_week_score`, `worst_week_score`,
    `made_playoffs`.
  - Built from: `stg__team_weeks` + `int__matchup_week_playoff_map` +
    `int__owner_team_year_map` + `int__team_postseason` (for `made_playoffs`).
  - Feeds: all Scoring metrics (season / matchup / playoff-snub).

- **`int__matchup_margins`** — game margins.
  - Grain: one row per played regular-season game.
  - Columns: winner/loser owner, `margin = abs(score_for - score_against)`, year, week.
  - Feeds: tightest matchups & biggest blowouts.

- **`int__lucky_records`** — luck classification (now defined, see §2 / §6.1).
  - Grain: one row per owner-week (regular season).
  - Columns: weekly score vs. league **median**, `is_lucky_win`, `is_unlucky_loss`,
    `luck_points` (= # of teams that outscored you on a win, negative on a loss).
  - **Primary focus = lucky-win / unlucky-loss *counts*** (the binary median flags).
    `luck_points` is built **alongside as an experimental side-metric** — surfaced so we
    can see whether the granular version turns into something interesting, but not the
    headline.
  - Feeds: lucky/unlucky title counts (primary), season luck totals + luckiest/unluckiest
    records (experimental).

- **`int__season_titles`** *(roll-up)* — per-season title resolution in one place.
  - Grain: one row per owner-season.
  - Columns: a boolean flag + an amount per title (scoring, non-scoring, matchup,
    bad-matchup, playoff snub, playoff luck-in, clutch win/lose, shotgun, no-shotgun).
  - Tie handling lives here: **co-titles** — every tied owner gets the flag (§6.3).
  - **Clutch title logic is isolated** (its own CTE / column block) so the naive ranking
    rule (§6.4) can be swapped without touching the rest of the model.
  - Feeds: both marts compose this so logic isn't duplicated.

### Marts (`marts/stats_center/league_highlights/`)

Both marts are **built**. The original `season_records` + `season_superlatives` stubs were
collapsed into a single `season_highlights` (same "rank within a season, take top-N" operation
at different N's). `top_n` (= 3) is a Jinja var at the top of each mart so the leaderboard depth
is trivially tweakable. ✅

- **`all_time_records.sql`** — the §3.1 catalog in **tidy/long** form (one row per
  metric × ranked owner), so the frontend filters by section/category without column
  sprawl. ✅ *Built.*
  - Columns: `section`, `category`, `metric_key`, `metric_label`, `metric_type`,
    `owner_id`, `owner_name`, `value`, `display_value`, `season_or_week`, `rank`.
  - A `metric_meta` VALUES table maps each `metric_key` → section/category/label/type plus
    `sort_sign` (+1 desc / −1 asc) and `result_n` (1 for single records, `top_n` for
    leaderboards). One ranked pool, one filter (`rank <= result_n`).
  - Records → a single row (`rank = 1`); leaderboards → `rank 1..N` (N = top-3, §6.5).

- **`season_highlights.sql`** — **one merged per-season tidy table**. ✅ *Built.*
  - Grain: one row per `year` × `metric_key` × `rank`.
  - Title holders come straight from the `int__season_titles` flags (co-titles included) via a
    struct-list `unnest` — one owner-season fans out to one row per title it holds.
  - Title metrics → `rank = 1` (co-title ties keep every holder); leaderboard metrics (tightest /
    blowouts) → `rank 1..N` (N = top-3, §6.5).
  - Columns: `category`, `metric_key`, `metric_label`, `metric_type`, `year`, `owner_id`,
    `owner_name`, `value`, `display_value`, `rank`, plus **nullable** `opponent_name` /
    `week` (populated only for game-grain leaderboard rows; null for owner-season titles).

> Contracts are enforced — every column needs `data_type:` in a sibling `properties.yml`
> before the build passes. Round all decimals for display in the mart.

### Build / verify loop

- `make run-dbt` — full-refresh + sqlfluff.
- `make run-pre-commit` — all hooks.
- Eyeball `int__owner_season_scoring` total-vs-PPG to inform the product decision in
  Decision #3.

---

## 5. Frontend plan (phase 2) — ✅ Built

Built as `frontend/stats_center/league_highlights.py` (single module, not a `home.py` dir) at
`/stats_center/league_highlights`. Two tabs — **All-Time** (record hero cards + medal leaderboards,
grouped by section → category) and **By Season** (`ui.select` year → `@ui.refreshable` panel of title
cards + tightest/blowout boards). See `frontend/FRONTEND.md`. Original plan below:

- Page at `/stats_center/league_highlights`,
  registered like the other stats-center subpages, `common_header()` first.
- **All-time** tab: record "cards" for the `record`/`amount` metrics + leaderboard tables
  for the `count`/`total` metrics, grouped by category (Scoring / Clutch / Matchups /
  Shotgun). Reuse `frontend/utils.table(...)`.
- **Season** tab: a season-picker dropdown (default = `int__current_season_year`) that
  drives a `@ui.refreshable` table of that season's title holders + amounts. Copy the
  `DropDownSelection` pattern from `strength_of_schedule.py` / `player_data.py`.
- Keep it thin — all logic stays in the marts; the page only `SELECT`s from
  `main_marts.all_time_records` / `main_marts.season_highlights`.

---

## 6. Open questions / TODO

**Resolved**

1. ~~**Lucky win definition**~~ → **Median-based** w/ luck points (§2 Decision #4). Modeled in
   `int__lucky_records`. ✅
3. ~~**Tie handling for titles**~~ → **Co-titles**: every tied owner gets the title (each
   count++). Resolved in `int__season_titles`. ✅
5. ~~**Leaderboard depth**~~ → **Top-3**, but parameterized (dbt var / single constant) so it's
   trivial to bump later. ✅

2. ~~**"Made the playoffs" derivation**~~ → **(a) Playoff matchup participation** is the source
   of truth: a team-season made the playoffs if it appears in any `is_playoff` matchup row in
   `base_s001__matchups`. Data quality is trusted here; if it proves unreliable we'll add a
   computed fallback (top `playoff_team_count` by standing) later. ✅
4. ~~**Clutch "record" semantics**~~ → **Naive v1: rank by clutch *win count*, tiebreak by clutch
   *win %***. Symmetric for the un-clutch record (loss count, tiebreak win %). We expect to
   iterate, so the logic is **isolated** in `int__season_titles` for easy swapping. ✅
7. ~~**Season-view `count` suffixes**~~ → Confirmed copy-paste artifacts. The season view shows the
   **title holder + amount** for that one season; cross-season *counts* only exist in the
   all-time view (e.g. season has "non-scoring title"; all-time has "non-scoring title count").
   ✅

8. ~~**Mart split**~~ → **Two long/tidy marts**: `all_time_records` + `season_highlights`. The
   season table is a single "rank within season, take top-N" table (titles = N:1,
   leaderboards = N:3), collapsing the old `season_records` / `season_superlatives` stubs. ✅

**Deferred product decision**

- **`total` vs `PPG` — which ships** → **deferred indefinitely; keep BOTH** (decision 1c).
  Neither compares like-for-like across seasons: season length varies (13 vs 14 games) *and*
  the active matchup roster size has changed over the years, so some seasons could score more
  *per game* regardless of length. Until we find a normalization that accounts for both, both
  columns stay in `int__owner_season_scoring` and the highlights surface both. For reference:
  by total #1 = Aditya 2023 (2052.8); by PPG #1 = Casey Magid 2018 (155.24).
