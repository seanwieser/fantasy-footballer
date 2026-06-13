# Frontend map (NiceGUI)

The page/route map for the web app — every route, the module that defines it, what it reads,
and the shared patterns — so you don't have to re-read every module to find things. The dbt
counterpart is [`dbt/fantasy_footballer/MODELS.md`](../../../dbt/fantasy_footballer/MODELS.md).

**Keep it current:** if you add/remove a page or route, change which marts a page reads, or add a
shared helper in `utils.py`, update the matching row/section here in the same change.

## Architecture & conventions

- **Page registration is by import side-effect.** Each page module runs an `@ui.page("/path")`
  decorator at import time. `main.py` imports every page module (that's the only reason for its
  `# pylint: disable=reimported,unused-import` — all the `home` imports shadow each other). **To
  add a page: create the module, then add it to the imports in `main.py`.**
- **Auth:** `AuthMiddleware` (`login/home.py`) gates all routes; `/login` uses bcrypt against
  `main_seed_data.users`. Every page calls `common_header()` first.
- **Access levels** (`get_access_level()` → public=0, member=1, admin=2). The **splash hub** (`SECTION_TILES`)
  is the only section nav — it gates each tile by `level <= access_level` (e.g. Gallery=1, Admin=2). The
  header (`common_header`) is just chrome: a home button, logout, and a shutdown button shown only to admins.
- **Filter-page pattern** (canonical: `strength_of_schedule.py`, `player_data.py` —
  copy one of these rather than reinventing). Per page:
  - a `<X>DropDownSelection` class — a `defaults()` classmethod, `reset()`, `get_filter(field)`
    returning a SQL fragment (`"ALL"` → `"1 = 1"`, else `field::varchar='value'`);
  - `filter_dropdown_button(...)`, `filter_ui(...)`;
  - `@ui.refreshable <name>_data_table(selection)` building SQL with `{selection.get_filter('field')}`
    interpolated into the `where`;
  - `refresh_table(selection, field, value)` setter + `.refresh()`;
  - `<name>_and_dropdowns()` composer; thin `page()`.
- **⚠️ No DB access at import time.** DB-dependent defaults (e.g. current year) must be resolved
  lazily in `defaults()`/`reset()` — **never** in a class-body `DEFAULT = {...}`. Class bodies run at
  **import**, and `main.py` imports every page before `app.on_startup(setup)` builds the DB, so an
  import-time query crashes a cold start against an empty/deleted `.duckdb`.
- **DB access:** always `DbManager.query(sql, to_dict=False)`. The frontend reads `main_marts.*` and
  `main_seed_data.*` only — never the intermediate/base/staging layers.
- **Tables:** build with `utils.table(df, ...)` (handles header formatting, `hidden_fields`,
  `not_sortable`, `pagination`, `slots`). f-string SQL interpolation is fine here (auth-gated app).

## `utils.py` — shared helpers

| Helper | Purpose | Reads |
|---|---|---|
| `common_header()` | Header chrome: home + logout (+ shutdown for admins). First call in every page. | — |
| `get_access_level()` | Current user's max page access level (public=0, member=1, admin=2). | — |
| `section_tile(label, icon, icon_color, route)` | Clickable nav tile (icon + label) for the splash hub grid. | — |
| `glossary_link(slug, …)` | Small clickable icon deep-linking to `/glossary#<slug>`; no-op on a falsy slug, so pass a nullable `glossary_slug` straight through. Used by metric cards (League Highlights / H2H / spotlight Highlights) to point at a concept's canonical definition. | — |
| `table(df, …)` | Standard `ui.table` component (format names, hide/lock cols, pagination, slots). | — |
| `format_field_name(name, …)` | snake_case → display title. | — |
| `get_current_year()` | Latest data year. | `main_marts.current_year` (col `year`) |
| `get_valid_years()` | `START_YEAR(2018)`..now. | — |
| `get_years_by_owner_id(owner_id?)` | Years with data, optionally for one owner. | `main_marts.owner_year_map` |
| `get_owner_names_by_year(year?)` | Owner names, optionally for one year. | `main_marts.owner_year_map` |
| `get_owners_by_year(year)` | `owner_id`+`owner_name` for a year (owner-switcher menu), sorted by name. | `main_marts.owner_year_map` |
| `get_nfl_teams()` | NFL team list. | `main_marts.nfl_teams` |
| `get_draftpicks_rounds()` / `…_round_picks()` | Draft round / round-pick options. | `main_marts.snake_draft_table` |
| `get_draft_type_years(is_auction)` | Years for snake vs auction. | `main_marts.{snake,auction}_draft_table` |
| `owner_id_to_owner_name(id)` | id → name. | `main_seed_data.owner_names` |
| `image_path_to_owner_id/name(path)` | gallery headshot path → owner. | — |
| `logout()` | Clear session, go to `/login`. | — |

Constants: `START_YEAR = 2018`, `VALID_POSITIONS = [QB, RB, WR, TE, D/ST, K]`,
`SECTION_COLORS` (section → Quasar color; covers League-Highlights sections plus the H2H-dashboard
`Record`/`Head to Head`/`The Rivalry`, and the shared `Postseason` + `Transactions` + `Lineups` (amber)
+ `Luck` (yellow) sections that both stats pages use),
`MEDALS` (rank → emoji) + `medal(rank)` (emoji or numbered
fallback) — shared by the League Highlights page, the H2H dashboard, and the owner-spotlight Highlights card.

## Pages

| Route | Module | Access | Marts / tables read | Notes |
|---|---|---|---|---|
| `/` | `splash/home.py` | public | — | **The hub.** A section-tile grid (`section_tile`) — the site's front door to every destination, driven by the `SECTION_TILES` list (gated by `get_access_level()`). Every destination is a top-level route (no stats_center grouping). |
| `/current_season` | `splash/current_season.py` | public | `current_standings`, `current_shotgun_counter` | Live standings + shotgun-counter tables (moved off the splash hub). Each row is **cross-linked** to that owner's spotlight for the current year via a `rowClick` reading the hidden `owner_id`. |
| `/login` | `login/home.py` | — | `main_seed_data.users` | `AuthMiddleware` + bcrypt login form. |
| `/owner_history` | `owner_history/home.py` | 0 | `owners_by_year` | Owner grid per year; links to spotlight. |
| `/owner_history/{owner_id}/{year}` | `owner_history/spotlight.py` | 0 | `season_overview`, `season_schedule`, `season_highlights`, `owner_weekly_lineup`, `postseason_schedule`, `owner_year_map` | Header is a paired **owner + year switcher** (two `dropdown_button`s grouped left: owner → another owner for the *same* year via `get_owners_by_year`; year → the same owner's other seasons via `get_years_by_owner_id`). Then `season_overview_card`s; queries `where owner_id=.. and year=..` (guards empty → "No season data" before `[0]`). **Highlights card** (`highlights_card`) lists that owner-year's podium finishes from `season_highlights` (medal by `rank`, value tinted by `SECTION_COLORS`, subtitle = the mart's precomposed `detail`); empty-state when none. Below the overview sits a **tabbed section** (`ui.tabs`, consistent `min-height`) with three tabs: **Regular Season** (`season_schedule_table`) — the dense `table()` q-table with a `body-cell-Highlights` slot rendering one section-colored chip (icon + tooltip) per active week flag, driven by `SCHEDULE_FLAGS` (flag → icon/section/label), the boolean flag columns from `season_schedule` passed as `hidden_fields` and read by the slot; **each row is clickable** (`on_week_click`) and jumps the Roster tab to that week. **Roster** (`weekly_roster_view`) — a `ui.select` keyed by **matchup_week** (+ **All**; playoff weeks borrow the Postseason tab's round label, e.g. `TB Round 1`, so the two selectors read identically) driving an actual-vs-optimal lineup view from `owner_weekly_lineup`: per NFL week, two columns (`_lineup_column`) by `LINEUP_SLOT_ORDER` with the started-but-suboptimal players marked red (left accent border + bright accent text, readable on the dark page) and the should-have-started bench players marked green, plus that week's **points left on the bench** (`_week_lineup_block`). A 2018-2019 two-week playoff matchup renders **both NFL-week lineups stacked** under a combined points-left banner. **All** renders the season roster (`_season_roster` from `owner_roster_production`: player names + Weeks/Started/Rostered Pts/Started Pts/Util%). (The dedicated per-player page is `/roster_production`.) **Postseason** (`postseason_schedule_table`) — that owner-season's bracket games (`postseason_schedule`: round label, opponent team + owner, both scores); **each row is clickable** and jumps the Roster tab to that matchup (a two-week 2018-2019 matchup opens both NFL-week lineups), gated by `roster_weeks`. Empty state when the owner missed the bracket. |
| `/postseason_history` | `postseason_history.py` | 0 | `postseason_timeline`, `postseason_trophy_case`, `postseason_bracket`, `postseason_snub_luck` | Three tabs: **Brackets** (season `ui.select` → `@ui.refreshable` panel rendering the winners + toilet brackets as columns of `_matchup_card`s, one column per `round_num`; bye slots show a lone team + "BYE", championship game gets a colored border. Each card highlights the **advancer** via `advancer_owner_id` — the winner in the championship bracket but the **loser** in the toilet bowl. Below them `_snub_luck_lists` renders side-by-side **Snubs** / **Lucky-In** columns from `postseason_snub_luck`, using the platform-canonical definitions), **Timeline** (newest-first grid of `_season_card`s — each season's four finishers 🥇🥈🥉🚽 with reg-season seed), **Trophy Case** (single dense column of slim `_trophy_card` rows, most-decorated first, medal tallies + playoff record). All sections use `SECTION_COLORS["Postseason"]` (teal); local `_headshot` helper. **Every owner on the page is a cross-link** — finisher rows, bracket participants, snub/lucky cards, and trophy cards all navigate to that owner's spotlight (`_link_to_owner` adds `cursor-pointer`/hover + `ui.navigate.to`), keyed by the row's season (trophy case uses the owner's `last_year`). |
| `/player_data` | `player_data.py` | 0 | `player_data_table` | Filter pattern (year / position / …). |
| `/strength_of_schedule` | `strength_of_schedule.py` | 0 | `strength_of_schedule` | **Canonical** filter pattern (year, owner_name). Each row **cross-links** to that owner's spotlight for the row's year via `rowClick` reading the hidden `owner_id`. |
| `/roster_production` | `roster_production.py` | 0 | `owner_roster_production` | Filter pattern (year / owner_name / position) over per-player roster production. Columns: Weeks/Started, **Rostered Pts** (scored while held), **Started Pts** (scored in lineup — what the team benefited from), **Total Pts** (player's full season), **Capture %** (started ÷ total) and **Roster Util %** (started ÷ held). A collapsible `legend()` glossary (`COLUMN_GLOSSARY`) explains each. Rows cross-link to the owner spotlight (`rowClick` + hidden `owner_id`). |
| `/glossary` | `glossary.py` | 0 | `glossary` | The platform **lexicon**: a searchable page (`ui.input` filter → `@ui.refreshable term_sections`) of ~55 concept definitions grouped into category sections (`CATEGORY_ORDER`, colored via `SECTION_COLORS`). Each term card has an anchor `id=<slug>` for deep-linking (`/glossary#<slug>`, scrolled-to on load via a one-shot `ui.timer`), the full definition, and `related`-term cross-link chips (`_scroll_to`). Reads `main_marts.glossary` (the `glossary_terms` seed). The single source of truth for terminology; metric cards across the app link here via `glossary_link()` using the metric's `glossary_slug`. |
| `/league_highlights` | `league_highlights.py` | 0 | `all_time_records`, `season_highlights`, `owners`, `main_seed_data.season_highlight_metrics` | Two tabs (**All-Time** / **By Season**), each split by a **secondary section sub-tab group** (`_section_subtabs`, one tab per `SECTIONS` entry — Scoring/Postseason/Matchups/Luck/Lineups/Shotgun/Clutch/Transactions, in that order, Luck between Matchups and Lineups) so neither view is one long scroll. **All-Time**: each section's panel (`all_time_section`) groups cards by `category` into scannable sub-clusters (e.g. Scoring → Full Season / Single Week / Playoff Races; single-category sections get no sub-header). **By Season**: a `ui.select` year above stable section tabs; each section panel is an `@ui.refreshable` (`render_season_section`) that re-queries just that section's holders on year change (so the active section is preserved across years). The grid is driven by the `season_highlight_metrics` catalog so a title with no holder that year still renders an `empty_card` placeholder (the seed's `empty_label`, e.g. "Everyone shotgunned this season"). Held titles render as one unified **`podium_card`** (medal-ranked grid, rank 1 carries a headshot, values aligned in a column), `description` tooltips, a `(retired)` tag from `owners.is_active`, and a per-row subtitle driven by the seed's `subtitle_kind`: season-award counts list the years won (`years_won`), career accumulations show seasons-played (from `owners.seasons_played`), single records show their year/week/opponent context. A **Transactions** section (in both tabs) surfaces career (`most_acquisitions_career`/`most_trades_career`) and per-season (`most_acquisitions_season`/`most_trades_season`) roster-move leaders. A **Postseason** section (mirroring the H2H dashboard's, per CLAUDE.md — the two pages stay organized the same way) holds the championships/playoff-appearances/toilet-bowl records (All-Time), and the per-season **Champion** / **Toilet Bowl Loser** titles shown with the owner's reg-season seed (By Season). A **Luck** section (yellow, mirrored on H2H) consolidates the league's whole luck story, all rooted in a **single definition** — the per-week all-play standing (`int__all_play_records`) — presented three ways across three categories: *Schedule Luck* (the continuous view: luckiest/most-robbed season + career `schedule_luck` = actual − expected wins, plus the merit-based all-play snub/lucky-in titles), *Matchup Luck* (the quantized view: career lucky-win / unlucky-loss week counts — won/lost a week you'd have lost/beaten most of the league), and *Playoff Luck* (the snub/lucky-in family — biggest snub/lucky-in + career counts). Moved here out of Matchups/Postseason. A **Lineups** section (amber) holds **two complementary per-season title pairs** — *Fewest / Most points left* (absolute reg-season points left on the bench vs optimal) and *Most / Least efficient lineup* (the share of the optimal captured) — plus the **Most underutilized player** title (the best player most left on the bench that season, with the player named in the subtitle). All-Time mirrors these with title counts, single-season points-left + efficiency records, and the biggest-ever single player-season bench waste. |
| `/h2h_dashboard` | `h2h_dashboard.py` | 0 | `h2h_owner_metrics`, `h2h_matchup_records`, `owners`, `main_seed_data.h2h_rivalry_metrics` | Multi-select owner picker (+ clear button) → `@ui.refreshable grid` calling `render_comparison`: a metric-rows × owner-columns CSS grid (label col + one column per selected owner), always showing every metric. Rows group by `section` (colored `section_header_cell`, reusing `SECTION_COLORS`); each cell shows `display_value` with the leader (`max(metric_value * sort_sign)`, suppressed when all tie) starred ⭐ in the section color. Single-record career metrics (`biggest_blowout`, `best_week_ever`, `worst_week_ever`, `highest_scoring_season`) carry context in parens via the mart's `override_display`. A **Transactions** section adds per-owner career acquisitions/trades, a **Luck** section (yellow, mirroring League Highlights) the per-owner all-play win % / career schedule luck / expected wins + the snub/lucky-in and lucky/unlucky career stats, and a **Lineups** section the per-owner lineup-setter title counts (both the points-left and efficiency pairs). The two lead pairwise sections render **only when exactly two owners are selected** (with 3+, a muted "select exactly two" note replaces them and just the career sections show). Their **row catalog (label/tooltip/order/kind) is the `h2h_rivalry_metrics` seed**, read by `_rivalry_catalog()` and rendered generically by `pair_section` — `metric_key` doubles as the `h2h_matchup_records` column and `pair_section` passes the section's `SECTION_COLORS` colour to the row renderers. Two render kinds: `symmetric` (`h2h_shared_row` — one value centered across both columns, with an `arrow_back`/`arrow_forward` icon toward the nullable `<metric_key>_leader` owner_id, none when even/tied; the mart formats these **owner-perspective** so reading the left owner's row already orders the value left→right by column); `per_owner` (`h2h_metric_row` — each owner's own independent value per column). **The Rivalry** leads (series record, playoff record, points/differential, avg margin, current streak, last meeting, clutch, closest game, highest shootout, lowest slugfest); below it **Head to Head** (avg score, longest win streak, biggest win, held-under-100, lucky wins, unlucky losses). All sourced from `h2h_matchup_records`. Each pair row has the same info-icon tooltip as the career rows. The Rivalry color is `pink`, Head to Head is `cyan` (chosen for dark-mode contrast). Picker defaults empty; needs ≥2 owners. |
| `/draft_analysis` | `draft_analysis/draft_analysis.py` | 0 | — (composes) | Tabs of two sub-modules ↓. |
| ↳ snake | `…/draft_analysis/snake_draft_table.py` | — | `snake_draft_table` | Own `SnakeDraftDropDownSelection`. Rows **cross-link** to the owner's spotlight for that draft year (`rowClick` + hidden `owner_id`). |
| ↳ auction | `…/draft_analysis/auction_draft_table.py` | — | `auction_draft_table` | Own `AuctionDraftDropDownSelection`. Rows **cross-link** to the owner's spotlight for that draft year (`rowClick` + hidden `owner_id`). |
| `/gallery` | `gallery/home.py` | 1 | media (owner headshots) | `resources/media/owners/<id>.jpg`. |
| `/admin` | `admin/home.py` | 2 | — | Ingest / transform / add user / shutdown; log streaming via `multiprocessing` queue. |

## Lookup marts (`main_marts.current_year` / `owner_year_map` / `nfl_teams`)

Dropdown-option lookups, now proper marts under `dbt/.../models/marts/utilities/` (see MODELS.md):
`current_year` (col `year`), `owner_year_map` (`owner_id`, `owner_name`, `year`), `nfl_teams`
(`nfl_team`, incl. the `'None'` free-agent sentinel). These replaced the old orphaned
`main_utilities.*` schema (deleted from dbt in PR #26, 2025-11-07, but never repointed until now). The
stale `main_utilities.*` tables may still linger in an existing local `.duckdb` — harmless and unused;
they vanish on a fresh build (or drop manually with `drop schema main_utilities cascade`).
