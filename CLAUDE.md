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
  macros/                       (currently empty)

resources/
  dbt_seeds/*.csv               truncated in git; populated at boot from B2
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
| `seeds`        | `seed_data`         | CSV in `resources/dbt_seeds/`       | `owner_names`, `display_names`, `users` (auth). |

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

- One `properties.yml` per directory (next to the SQL files).
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

Prefer these over inline SQL tests.

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
5. Run `make run-dbt` (full-refresh + sqlfluff). Then `make run-pre-commit`.

## Python conventions

### Pages

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

## Local dev

```bash
make run-local              # poetry run python3 src/fantasy_footballer/main.py
make run-local ARGS=--dev-mode   # skip the boot data fetch if seeds are populated
make run-dbt                # local dbt build (target=default, path is ../../resources/...)
make run-pre-commit         # all hooks
make truncate-dbt-seeds     # empty seed CSVs (run BEFORE committing)
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

`run-local` will block on data ingest the first time (downloads cloud data, runs
dbt). Pass `--dev-mode` after the first run if the seed CSVs are populated — it
skips ingest entirely and reuses the existing `.duckdb` file.

The dbt `default` target uses path `../../resources/...` (run from `dbt/fantasy_footballer/`),
while `app` target uses `./resources/...` (run from repo root by the Python app).
That's why `make run-dbt` and `DbManager.run_dbt` use different `--target`s.

## Gotchas / don'ts

- **Never commit populated seed CSVs.** `resources/dbt_seeds/*.csv` contain real
  owner data + auth hashes. Run `make truncate-dbt-seeds` before committing if
  you've booted the app locally. The README also calls this out.
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
