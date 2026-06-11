# fantasy-footballer

A web app for an ESPN fantasy-football league (~12–15 members) to explore historical
league + NFL data through dashboard-style pages. All analytics are precomputed in
dbt at app boot; the frontend only issues thin `SELECT`s and renders the results.

## Architecture at a glance

```
ESPN API (espn_api)            Backblaze B2 (S3-compatible)            DuckDB (local file)            NiceGUI page
   │                                  │                                       │                            │
   ▼                                  ▼                                       ▼                            ▼
S001Extractor ──► raw JSON ──► resources/data/sources/... ──► main.<source>.<table> ──► dbt build ──► main_marts.*
   (pydantic schemas)                                                                  (full-refresh)
```

Boot path (`DbManager.setup`, see `src/fantasy_footballer/backend/db.py`):
1. `fetch_resources` — pull freshest seeds + media from B2 to local `resources/`.
2. `ingest_raw_data_from_cloud` — for each source, `CREATE OR REPLACE TABLE` from
   the latest cloud JSON files into `main.<source>.<table>`.
3. `run_dbt` — `dbt build --full-refresh --target app` materializes every layer as
   tables in the same DuckDB file the frontend queries.

The frontend never recomputes analytics; it just calls `DbManager.query(sql)`.

## Tech stack

- **Python 3.12.5** managed by **Poetry**. Single package: `src/fantasy_footballer`.
- **NiceGUI** (with FastAPI + Uvicorn under the hood) for the web UI.
- **dbt-core 1.10 + dbt-duckdb 1.9** for all analytics.
- **DuckDB 1.4** as the single local analytical store (`resources/fantasy_footballer.duckdb`).
- **Pydantic** schemas in each source transformer.
- **Backblaze B2** for object storage (raw source JSON, seeds, media), accessed via boto3.
- **Fly.io** for hosting (`fly.toml`).

## Repo layout

```
src/fantasy_footballer/
  main.py                       entry point: builds DbManager, wires auth, ui.run(...)
  backend/
    db.py                       DbManager (static methods) — the ONLY DB interface
    utils.py                    Transformer base class, S3 client, write helpers
    sources/<src>/extract.py    per-source Extractor (declares ALL_TRANSFORMERS)
    sources/<src>/transformers/ one file per source table; pydantic schema + Transformer
  frontend/
    utils.py                    common_header, table(...), query helpers, dropdown helpers
    splash/home.py              "/"          (landing)
    stats_center/home.py        "/stats_center" + one module per subpage
    owner_history/home.py       "/owner_history" + spotlight.py for "/owner_history/{owner_id}/{year}"
    gallery/home.py             "/gallery"
    admin/home.py               "/admin" (ingest, transform, add user, shutdown)
    login/home.py               "/login" + AuthMiddleware
  groupme/app.py                standalone GroupMe puller (not part of NiceGUI app)

dbt/fantasy_footballer/
  dbt_project.yml               schemas + +materialized: table + +contract: enforced
  profiles.yml                  default duckdb profile (default vs app target — path differs)
  models/{base,staging,intermediate,marts}/...
  tests/generic/                custom generic tests
  macros/                       format_metric_value (shared display formatting for the metric-catalog marts)
  seeds/*.csv                   git-TRACKED constant seeds (non-sensitive metadata, e.g. league_highlights metric catalogs)

resources/
  sensitive_seeds/*.csv         git-ignored (all of resources/); SENSITIVE seeds (owner data, auth) populated at boot from B2
  fantasy_footballer.duckdb     built locally; never committed
  media/owners/<owner_id>.jpg   owner headshots
```

## dbt conventions (read this before editing any model)

The dbt project is the heart of this codebase. Patterns here are deliberate — match
them when adding models.

**Before working in dbt, read [`dbt/fantasy_footballer/MODELS.md`](dbt/fantasy_footballer/MODELS.md)**
— the data-model map (every model's grain, purpose, key columns, upstream refs, and the
non-obvious data gotchas). It exists so you don't have to re-inspect every `.sql` file.
**Keep it current: if you add, remove, or materially change a model (grain, purpose, key
columns, or upstream refs), update its entry in MODELS.md in the same change.**

### Layer responsibilities

| Layer          | Schema (`main_<x>`) | Filename                            | Purpose |
|----------------|---------------------|-------------------------------------|---------|
| `base/<src>/`  | `base`              | `base_<src>__<table>.sql`           | 1:1 with sources. Cast types, rename to snake_case, compute composite IDs (`team_year_id`, `player_year_id`, etc.), pass through `meta__*` columns. No joins to other refs. |
| `staging/`     | `staging`           | `stg__<entity>.sql`                 | Unnest arrays/structs, flatten weekly grain, light enrichment via joins to other `base_*` or seeds. Flat tables, no business logic. |
| `intermediate/`| `intermediate`      | `int__<concept>.sql`                | Reusable computations referenced by multiple marts (`int__owner_team_year_map`, `int__strength_of_schedule`, `int__current_season_year`, etc.). |
| `marts/<page>/`| `marts`             | `<table>.sql` (no prefix)           | Page-specific final tables. Dir structure mirrors the frontend page that consumes it (e.g. `marts/stats_center/draft_analysis/snake_draft_table.sql` ↔ `frontend/stats_center/draft_analysis/snake_draft_table.py`). Do display formatting here (rounding, `owner_name` lookup, column renames) so the frontend stays thin. |
| `seeds`        | `seed_data`         | CSV in `resources/sensitive_seeds/` (sensitive, gitignored) or `dbt/.../seeds/` (constants, git-tracked) | Sensitive: `owner_names`, `display_names`, `users` (auth). Constant/git-tracked: `all_time_record_metrics`, `season_highlight_metrics`. Both land in `main_seed_data`. `seed-paths` lists both dirs. |

The double underscore (`__`) is intentional — it separates the layer-prefix from the
entity name. Don't change to single underscore.

### Materialization & contracts

Set globally in `dbt_project.yml`:

```yaml
+materialized: table        # everything is a table (we full-refresh on boot)
+contract: { enforced: true } # column data_types in properties.yml are enforced
```

This means **every column in every model must be declared with `data_type:` in the
matching `properties.yml`**, or the build fails. When adding a column, update
properties.yml first.

### properties.yml conventions

- **One yml file per model**, named exactly like the SQL file, living in a `properties/`
  subdir of that model's layer directory — e.g. `models/intermediate/int__season_titles.sql`
  → `models/intermediate/properties/int__season_titles.yml`. (We split the old consolidated
  `properties.yml` files because the model count per layer grew too large.) Each file is a
  standalone `version: 2` + `models:` doc containing that one model's block.
- **Seeds follow the same pattern**: one yml per seed in `dbt/fantasy_footballer/seeds/properties/`
  (a standalone `version: 2` + `seeds:` doc), named like the seed — e.g. `owner_names.yml`,
  `all_time_record_metrics.yml`. (dbt parses these regardless of where the seed CSV lives, so the
  sensitive seeds in `resources/sensitive_seeds/` are documented here too.)
- **No top-of-file description comments in `.sql` models.** The model description lives only in
  the yml `description:` key. Keep it concise, convey the model's spirit, and **lead with the
  grain** (e.g. "One row per owner-season ..."). No issue/PR numbers. Genuine mid-file comments
  that explain non-obvious *logic* are still fine.
- **Never collapse `data_tests` to an inline array.** Always one test per line:
  ```yaml
  data_tests:
    - not_null
    - unique
  ```
  not `data_tests: [ not_null ]`.
- Use `data_tests:` (newer dbt syntax). Some older models still use `tests:` — match
  the file you're editing rather than mixing both in one model block.
- Lean heavily on `relationships` tests for join integrity:
  ```yaml
  - relationships:
      arguments:
        to: ref('base_s001__teams')
        field: team_year_id
  ```
- Composite IDs (`team_year_id`, `team_week_id`, `player_year_id`, `player_week_id`,
  `owner_year_id`) are the standard join keys — declare them `unique` + `not_null`
  where they're the grain.
- Multi-line descriptions use `>` folded blocks.

### Custom generic tests (`tests/generic/`)

- `assert_model_has_rows` — model is non-empty. Used on seeds.
- `test_average_equals(value, tolerance=0.01, allow_null=false)` — sanity-checks
  computed averages (e.g. league-wide OW should average 0.5).
- `test_range(min_value, max_value, inclusive=true, allow_null=false)` — bounds check.
- `assert_all_values_present(to, field)` — inverse of `relationships`: every value of the
  tested column must appear in `to.field`. Used on the metric-catalog seeds to assert no
  orphan rows (every `metric_key` produces at least one mart row).

Prefer these over inline SQL tests.

**Cross-mart consistency (singular) tests** in `tests/*.sql` guard invariants that span models —
the genre to extend when two marts should agree. Current set: `assert_matchup_titles_match_week_chips`
(chip↔title), `assert_h2h_extremes_within_league_records` (rivalry extremes bounded by league records),
`assert_postseason_placements_match_espn`, `assert_career_record_matches_source` (H2H-summed record ↔
raw ESPN `base_s001__teams`), `assert_league_reg_season_zero_sum` (per-season wins=losses & PF=PA), and
`assert_matchup_margins_arithmetic` (`margin`/`combined` definitions).

### SQL style

Match the existing models exactly — sqlfluff (duckdb dialect, dbt templater) runs in
pre-commit and enforces most of it. Key conventions:

- Lowercase keywords, snake_case identifiers. Max line length 120.
- **Explicit casts everywhere** in `base/` models, even for already-correct types:
  `wins::int as wins`. This makes the schema contract obvious in the SQL itself.
- CTE-driven, one concept per CTE. End with `select * from <last_cte>`.
- Composite IDs are built with `||`:
  `team_id::varchar || '_' || year::varchar as team_year_id`.
- Reference upstream models with `{{ ref("...") }}`; sources with `{{ source("s001", "...") }}`.
- When a model self-joins (very common with `stg__team_weeks` for opponent lookup),
  alias by role: `team_weeks` + `opponent_weeks`, not `t1`/`t2`.
- DuckDB-specific features in active use — prefer these over generic SQL:
  `unnest(...)`, `array_value(...)`, `list_filter(arr, lambda x: ...)`, `list_aggr`,
  `array_agg({...})`, `if(cond, a, b)`, `try_cast`, `count_if(...)`, `unpivot`,
  struct/map array types in column declarations.
- When sqlfluff complains about a valid DuckDB construct (lambdas, unnest in select
  list), suppress with inline `--noqa` rather than disabling the rule globally.
- Every `base_*` carries `meta__source_path`, `meta__date_effective`, `meta__date_pulled`
  through unchanged — these power `stg__source_metadata` and `int__source_freshness`.

### Layer-specific idioms

- **`base/`**: a single `select` from a single `{{ source(...) }}`. No CTEs unless
  you're unioning (see `base_s001__matchups.sql` splitting home/away). No `ref` calls.
- **`staging/`**: usually `<entity>_unnested` → `<entity>_expanded` → `<entity>_enriched`
  CTE progression. This is where struct/array fields from base get flattened to rows.
- **`intermediate/`**: small, named after the concept (`int__shotguns`, `int__clutch_records`).
  These are the building blocks marts compose.
- **`marts/`**: join `int__owner_team_year_map` / `int__owner_team_map` to surface
  `owner_name` / `owner_id`. Cross-join `int__current_season_year` for "current"
  views (see `marts/splash/current_standings.sql`). Round decimals for display.

### "Current season" pattern

`int__current_season_year` is `select max(year) as current_season_year ...` —
single-row. Cross-join it into any mart that should auto-update each year:

```sql
from {{ ref("base_s001__teams") }} as teams
cross join {{ ref("int__current_season_year") }} as current_year
where teams.year = current_year.current_season_year
```

Never hard-code the current year.

### Adding a new mart

1. Create `models/marts/<page>/<table>.sql` matching the frontend page path.
2. Add a `properties.yml` entry next to it with descriptions + `data_type:` for
   every column (contracts are enforced).
3. If it needs reusable logic, factor into `models/intermediate/int__*.sql` first.
4. Update `dbt/fantasy_footballer/MODELS.md` with the new model(s) (and any new
   intermediate) — grain, purpose, key columns, upstream.
5. Run `make run-dbt` (full-refresh dbt build). Then `make run-pre-commit` (runs sqlfluff + the Python hooks).

## Python conventions

### Pages

**Before working in the frontend, read [`src/fantasy_footballer/frontend/FRONTEND.md`](src/fantasy_footballer/frontend/FRONTEND.md)**
— the page/route map (every route, its module, access level, which marts it reads, and the shared
`utils.py` helpers + filter-page pattern). It exists so you don't have to re-read every module.
**Keep it current: if you add/remove a page or route, change which marts a page reads, or add a
shared `utils.py` helper, update FRONTEND.md in the same change.**

**Cross-link the platform.** Always look for sensible opportunities to connect pages — wherever an
owner, season, matchup, or player appears, make it a link to the relevant destination (e.g. an owner
name → their owner-spotlight `/owner_history/{owner_id}/{year}`, a season → that season's view). The
app is a web of interrelated views, and the navigation between them is a core part of the UX; a name
that *could* link somewhere useful generally should. Prefer making the whole card/row clickable
(`.on("click", lambda: ui.navigate.to(...))` + `cursor-pointer`) over a bare underlined link when the
element is card-shaped.

Every NiceGUI page module follows the same shape:

```python
@ui.page("/some/path")
def page():
    common_header()
    ...
```

For pages with filters + table, the recurring pattern is:

- `DropDownSelection` class with a `DEFAULT` dict, `reset()`, `get_filter(field)`
  returning a SQL fragment (`"ALL"` → `"1 = 1"`).
- `@ui.refreshable` `<name>_data_table(selection)` that builds the SQL with
  `{selection.get_filter('field')}` interpolated into a `where ... and ...` clause.
- `filter_dropdown_button` / `filter_ui` helpers.
- `refresh_table(selection, field, value)` setter + refresh.
- `<name>_table_and_dropdowns()` composes the above.

See `frontend/stats_center/player_data.py` or
`frontend/stats_center/strength_of_schedule.py` for the canonical version. Copy
that file rather than reinventing.

### Database access

**Before working in the backend, read [`src/fantasy_footballer/backend/BACKEND.md`](src/fantasy_footballer/backend/BACKEND.md)**
— the backend map (the two data paths — extract ESPN→B2 vs ingest B2→DuckDB; the boot lifecycle;
the `DbManager` method reference; the source/transformer table; cloud-storage layout; env vars). It
exists so you don't have to re-read `db.py` / `utils.py` / every transformer. **Keep it current: if
you add/remove a `DbManager` method, change the boot path, add a source or transformer, or change the
cloud layout/env vars, update BACKEND.md in the same change.**

- All queries go through `DbManager.query(sql, to_dict=False)`. Never instantiate
  `duckdb.connect` from a frontend module.
- Schemas as seen from the frontend (default DuckDB catalog is `main`):
  `main_marts.*`, `main_intermediate.*`, `main_staging.*`, `main_base.*`,
  `main_seed_data.*`.
- The frontend uses f-string SQL interpolation freely — this is acceptable here
  because the app is auth-gated to ~15 known users. Don't introduce raw user input
  into SQL without thinking about it, but don't add ORM-style abstraction either.

### Adding a new source

A "source" = one upstream data provider (currently just `s001` = ESPN). To add one:

1. `src/fantasy_footballer/backend/sources/<src>/transformers/<table>.py` — one file
   per table, each with a `pydantic.BaseModel` schema and a `Transformer` subclass
   declaring `TABLE_NAME` + `TABLE_SCHEMA` and overriding `transform(queue)`.
2. `src/fantasy_footballer/backend/sources/<src>/extract.py` — `<Src>Extractor` class
   with `SOURCE_NAME`, `ALL_TRANSFORMERS = [...]`, and `run(queue, years, tables)`.
3. Register it in `db.py`: `SOURCE_EXTRACTOR_MAP = {e.SOURCE_NAME: e for e in [...]}`.
4. Add `dbt/.../models/base/<src>/base_<src>__<table>.sql` + `sources.yml` entry +
   `properties.yml`.
5. Downstream `staging/`, `intermediate/`, `marts/` consume the new base models.

### Style

- pylint config in `pyproject.toml`: line-len 120, `import-error` / `no-member`
  disabled (NiceGUI dynamic attrs). Snake_case enforced.
- pydocstyle: module + function docstrings required (with D107, D203, D212, D401
  ignored). Tests, utils, examples are excluded.
- isort runs in pre-commit.
- All inline pylint disables should be narrow and commented. There are existing
  examples (`# pylint: disable=broad-exception-caught`) — follow that style.
- **Inline comments (code, SQL, and config) describe the current state/intent, not the
  change that produced it.** Diff-narrating phrasing — "now lives in…", "moved from…",
  "removed the X flag" — goes stale the moment the next change lands and the reader has no
  diff in hand. Write what the code *is/does*, or drop the comment if the code already says it.

## Local dev

```bash
make run-local-fresh        # full boot: fetch cloud data + dbt build, then run
make run-local-dev          # --dev-mode: skip the boot data fetch if seeds are populated
make run-dbt                # local dbt build (target=default, path is ../../resources/...)
make push-sensitive-seeds   # upload local resources/sensitive_seeds/*.csv to B2 (needs .envrc creds)
make run-pre-commit         # all hooks
make build && make up       # docker run on :8080 (requires image/.env)
make down                   # tear down container

make query SQL="select ..."             # read-only ad-hoc query against the warehouse
make query FORMAT=csv SQL="select ..."   # FORMAT = table (default) | csv | json
```

### Inspecting the warehouse (`scripts/query_db.py`)

To eyeball model output without booting the app, use the read-only query helper. It opens
the DuckDB file `read_only` (can never mutate it) and prints the result. Good for both
humans and agents verifying a new model:

```bash
make query SQL="select * from main_intermediate.int__owner_season_scoring limit 10"
poetry run python3 scripts/query_db.py "select count(*) from main_marts.current_standings"
echo "select 1 as x" | poetry run python3 scripts/query_db.py -   # SQL from stdin
```

Schemas as seen here match the frontend: `main_marts.*`, `main_intermediate.*`,
`main_staging.*`, `main_base.*`, `main_seed_data.*`. This is the preferred way to spot-check
data — don't hand-roll one-off `duckdb.connect(...)` Python each time.

`make run-local-fresh` will block on data ingest (downloads cloud data, runs dbt).
Use `make run-local-dev` after the first run if the seed CSVs are populated — it
passes `--dev-mode`, skipping ingest entirely and reusing the existing `.duckdb` file.

The dbt `default` target uses path `../../resources/...` (run from `dbt/fantasy_footballer/`),
while `app` target uses `./resources/...` (run from repo root by the Python app).
That's why `make run-dbt` and `DbManager.run_dbt` use different `--target`s.

## Feature backlog (project management)

Future work is tracked in [`docs/feature-backlog.md`](docs/feature-backlog.md) — a lightweight,
in-repo backlog (not GitHub Issues). When asked to add/triage/update backlog items, follow its
conventions:

- **IDs are `FF-XXX`** (zero-padded, **assigned in strict order, never reused**). New item → next
  number after the highest existing id.
- **Two places per item, always kept in sync:** a row in the top **Index** table *and* a detail
  section below. Adding, editing status/priority/effort, or renaming an item means updating
  **both** the Index row and the item's metadata header line.
- **Fields are fixed** (see the doc's `Fields` legend): `Area` (multi-valued), `Priority`
  (`Low`/`Med`/`High`), `Effort` (`S`/`M`/`L`), `Status` (`Idea`/`Ready`/`Doing`/`Done`), and a
  one-line **Done when**. Don't invent new fields or values without asking — the point is to stay
  small.
- **Finishing an item:** set `Status: Done` and move its section to the bottom of the doc.
- **Architecture-level direction** (not discrete features) lives in
  [`docs/architecture-roadmap.md`](docs/architecture-roadmap.md), not the backlog.
- **Open questions / decisions to discuss** (often with the league, not yet actionable) live in
  [`docs/open-discussion.md`](docs/open-discussion.md), with `OD-XXX` ids. Resolved ones graduate to
  the backlog or are decided and removed.
- **Settled data investigations** (analyses we ran and concluded — especially ones we chose *not* to
  build) live in [`docs/investigations.md`](docs/investigations.md), with `INV-XXX` ids. The point is to
  preserve the finding (and any league fact it surfaced) so it isn't re-derived from scratch.
- **Branch/commit convention:** branch `FF-00X-short-name`; reference the id in commit messages.

## Gotchas / don'ts

- **Sensitive seed CSVs hold real owner data + auth hashes** (`resources/sensitive_seeds/*.csv`).
  They are untracked and the whole `resources/` dir is git-ignored (`.gitignore`), so a
  plain `git add` can't stage them — only a deliberate `git add -f` would. Never force them in.
  (Non-sensitive *constant* seeds live in `dbt/fantasy_footballer/seeds/` and ARE git-tracked —
  only put metadata/constants there, never owner data or secrets.)
- **`.envrc` is git-ignored but contains real secrets** (B2 keys, ESPN cookies).
  Don't ever check it in, and don't surface its contents in agent output.
- **Contracts are enforced.** Adding/removing a column without updating
  `properties.yml` will fail the dbt build. Update both in the same change.
- **Don't add error handling that swallows errors.** Existing `# pylint: disable=broad-exception-caught`
  spots print SQL + re-raise; preserve that pattern when adding new DB calls.
- The `groupme/` module is a standalone script, not part of the NiceGUI app.
  Don't try to integrate it into `main.py`.
- `2018` data is special-cased in `MatchupTransformer` (uses `scoreboard` instead
  of `box_scores`). When working with matchup data, account for it.
- **League Highlights and the H2H Dashboard should stay organized the same way.** The two
  stats pages (`/stats_center/league_highlights` and `/stats_center/h2h_dashboard`) present the
  *same* league analytics from different angles — all-owner records/leaderboards + per-season
  titles vs. pairwise comparison — so they should share the same **sections** (Scoring,
  Postseason, Matchups, Shotgun, Clutch, Transactions, …) and, for the most part, the same
  **metrics**. When you add or move a metric/section in one, mirror it in the other unless there's
  a clear reason not to. The alignment lives in the three seed catalogs (`all_time_record_metrics`,
  `season_highlight_metrics`, `h2h_metrics`) — keep their `section`/metric sets in sync.
- **Regular-season and playoff metrics are kept completely separate.** This league's
  playoff matchups are ~2-week aggregates, so a playoff "week" carries a score on a
  different scale (often ~2× a regular-season week). **Never mix playoff games into any
  score / margin / combined / average / streak metric** — they'd distort it and break
  comparability with the regular-season-only records. Every comparison metric
  (`int__owner_head_to_head` rivalry stats, the League-Highlights records via
  `int__matchup_margins`, season titles, etc.) is regular-season only; playoffs surface
  *solely* as their own separate W-L records (e.g. `playoff_wins`/`playoff_losses`).
  When adding a new score/margin metric, filter to `not is_playoff` and, if it has a
  league-wide counterpart, add a cross-model bound test (see
  `tests/assert_h2h_extremes_within_league_records.sql`).
