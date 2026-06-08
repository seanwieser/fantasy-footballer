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
- **Access levels** (in `common_header`, keyed by top-level section): `owner_history` & `stats_center` = 0
  (public), `gallery` = 1, `admin` = 2. User `public` sees level 0; `admin` sees all; any other user sees ≤ 1.
- **Filter-page pattern** (canonical: `stats_center/strength_of_schedule.py`, `stats_center/player_data.py` —
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
| `common_header()` | Top nav bar + access-level page filtering. First call in every page. | — |
| `table(df, …)` | Standard `ui.table` component (format names, hide/lock cols, pagination, slots). | — |
| `format_field_name(name, …)` | snake_case → display title. | — |
| `get_current_year()` | Latest data year. | `main_marts.current_year` (col `year`) |
| `get_valid_years()` | `START_YEAR(2018)`..now. | — |
| `get_years_by_owner_id(owner_id?)` | Years with data, optionally for one owner. | `main_marts.owner_year_map` |
| `get_owner_names_by_year(year?)` | Owner names, optionally for one year. | `main_marts.owner_year_map` |
| `get_nfl_teams()` | NFL team list. | `main_marts.nfl_teams` |
| `get_draftpicks_rounds()` / `…_round_picks()` | Draft round / round-pick options. | `main_marts.snake_draft_table` |
| `get_draft_type_years(is_auction)` | Years for snake vs auction. | `main_marts.{snake,auction}_draft_table` |
| `owner_id_to_owner_name(id)` | id → name. | `main_seed_data.owner_names` |
| `image_path_to_owner_id/name(path)` | gallery headshot path → owner. | — |
| `logout()` | Clear session, go to `/login`. | — |

Constants: `START_YEAR = 2018`, `VALID_POSITIONS = [QB, RB, WR, TE, D/ST, K]`,
`SECTION_COLORS` (highlight section → Quasar color), `MEDALS` (rank → emoji) + `medal(rank)`
(emoji or numbered fallback) — shared by the League Highlights page and the owner-spotlight Highlights card.

## Pages

| Route | Module | Access | Marts / tables read | Notes |
|---|---|---|---|---|
| `/` | `splash/home.py` | public | `current_standings`, `current_shotgun_counter` | Landing; standings + shotgun tables. |
| `/login` | `login/home.py` | — | `main_seed_data.users` | `AuthMiddleware` + bcrypt login form. |
| `/owner_history` | `owner_history/home.py` | 0 | `owners_by_year` | Owner grid per year; links to spotlight. |
| `/owner_history/{owner_id}/{year}` | `owner_history/spotlight.py` | 0 | `season_overview`, `season_schedule`, `season_highlights` | `season_overview_card`s; queries `where owner_id=.. and year=..` then `[0]`. **Highlights card** (`highlights_card`) lists that owner-year's podium finishes from `season_highlights` (medal by `rank`, value tinted by `SECTION_COLORS`, subtitle = the mart's precomposed `detail`); empty-state when none. **Schedule** (`season_schedule_table`) is the dense `table()` q-table with a `body-cell-Highlights` slot rendering one section-colored chip (icon + tooltip) per active week flag, driven by `SCHEDULE_FLAGS` (flag → icon/section/label); the boolean flag columns from `season_schedule` are passed as `hidden_fields` and read by the slot. |
| `/stats_center` | `stats_center/home.py` | 0 | — | Card grid (`stats_center_card`) linking subpages. |
| `/stats_center/player_data` | `stats_center/player_data.py` | 0 | `player_data_table` | Filter pattern (year / position / …). |
| `/stats_center/strength_of_schedule` | `stats_center/strength_of_schedule.py` | 0 | `strength_of_schedule` | **Canonical** filter pattern (year, owner_name). |
| `/stats_center/league_highlights` | `stats_center/league_highlights.py` | 0 | `all_time_records`, `season_highlights`, `owners`, `main_seed_data.season_highlight_metrics` | Two tabs: **All-Time** (each section's cards grouped by `category` into scannable sub-clusters — e.g. Scoring → Full Season / Single Week / Playoff Races; single-category sections get no sub-header) and **By Season** (`ui.select` year → `@ui.refreshable` panel: that year's title holders grouped under the same colored section headers via the seed's `section`/`display_order`, then a "Closest & Most Lopsided" margin-leaderboard block). The grid is driven by the `season_highlight_metrics` catalog so a title with no holder that year still renders an `empty_card` placeholder (the seed's `empty_label`, e.g. "Everyone shotgunned this season"). Held titles render as one unified **`podium_card`** (medal-ranked grid, rank 1 carries a headshot, values aligned in a column), `description` tooltips, a `(retired)` tag from `owners.is_active`, and a per-row subtitle driven by the seed's `subtitle_kind`: season-award counts list the years won (`years_won`), career accumulations show seasons-played (from `owners.seasons_played`), single records show their year/week/opponent context. |
| `/stats_center/draft_analysis` | `stats_center/draft_analysis/draft_analysis.py` | 0 | — (composes) | Tabs of two sub-modules ↓. |
| ↳ snake | `…/draft_analysis/snake_draft_table.py` | — | `snake_draft_table` | Own `SnakeDraftDropDownSelection`. |
| ↳ auction | `…/draft_analysis/auction_draft_table.py` | — | `auction_draft_table` | Own `AuctionDraftDropDownSelection`. |
| `/gallery` | `gallery/home.py` | 1 | media (owner headshots) | `resources/media/owners/<id>.jpg`. |
| `/admin` | `admin/home.py` | 2 | — | Ingest / transform / add user / shutdown; log streaming via `multiprocessing` queue. |

### Stubs — not built yet (`common_header()` + "Coming Soon...")

| Route | Module | Intended source |
|---|---|---|
| `/stats_center/h2h_dashboard` | `stats_center/h2h_dashboard.py` | — |
| `/stats_center/postseason_history` | `stats_center/postseason_history.py` | — |

## Lookup marts (`main_marts.current_year` / `owner_year_map` / `nfl_teams`)

Dropdown-option lookups, now proper marts under `dbt/.../models/marts/utilities/` (see MODELS.md):
`current_year` (col `year`), `owner_year_map` (`owner_id`, `owner_name`, `year`), `nfl_teams`
(`nfl_team`, incl. the `'None'` free-agent sentinel). These replaced the old orphaned
`main_utilities.*` schema (deleted from dbt in PR #26, 2025-11-07, but never repointed until now). The
stale `main_utilities.*` tables may still linger in an existing local `.duckdb` — harmless and unused;
they vanish on a fresh build (or drop manually with `drop schema main_utilities cascade`).
