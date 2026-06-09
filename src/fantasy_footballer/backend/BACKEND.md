# Backend map

How data gets into the DuckDB warehouse and how the app talks to it. Counterparts:
[`dbt/fantasy_footballer/MODELS.md`](../../../dbt/fantasy_footballer/MODELS.md) (analytics) and
[`frontend/FRONTEND.md`](../frontend/FRONTEND.md) (pages).

**Keep it current:** if you add/remove a `DbManager` method, change the boot path, add a source or
transformer, or change the cloud-storage layout / env vars, update this file in the same change.

## The key mental model: two separate data paths

These are easy to confuse — they move data in opposite directions and run at different times.

1. **Extract (ESPN → B2)** — *write* path, admin-triggered. Pulls fresh data from the ESPN API via
   `espn_api`, validates it through pydantic, and writes raw JSON to Backblaze B2. Code: `sources/`.
   Entry: `DbManager.fetch_data_from_sources` → `S001Extractor.run`. **Not part of normal boot.**
2. **Ingest + build (B2 → DuckDB → marts)** — *read/assemble* path, runs at every boot. Downloads the
   freshest B2 JSON, `CREATE OR REPLACE TABLE`s it into DuckDB, then runs dbt. Code: `db.py`.

The frontend never does either — it only calls `DbManager.query(sql)` against the built warehouse.

## Boot lifecycle (`DbManager.setup`, wired in `main.py` via `app.on_startup`)

`setup()` runs unless `--dev-mode` **and** seeds already populated (`has_sensitive_seeds_rows`), else:
1. **`fetch_resources()`** — list B2, pick the freshest date-partition per `resources/` dir, download
   to local `resources/` with the date stripped from the path (populates seeds + media).
2. **`ingest_raw_data_from_cloud(sources)`** — open `resources/fantasy_footballer.duckdb`, register the
   S3 secret (`SECRET_SQL`), and for each source/table `CREATE SCHEMA` + `CREATE OR REPLACE TABLE
   main.<source>.<table> AS SELECT *, '<date>' as meta__date_pulled FROM read_json(<freshest paths>)`.
3. **`run_dbt(action="build")`** — `dbtRunner` `build --full-refresh --target app` materializes every
   dbt layer as tables in the same `.duckdb` file.

## `DbManager` (`db.py`) — the ONLY DB interface (all static methods)

Constants: `DB_PATH = resources/fantasy_footballer.duckdb`, `SENSITIVE_SEEDS_PATH = resources/sensitive_seeds`,
`SOURCE_EXTRACTOR_MAP = {e.SOURCE_NAME: e}` (register new sources here).

| Method | Role |
|---|---|
| `setup()` | Boot orchestrator (the 3 steps above). Skips when dev-mode + seeds present. |
| `query(sql, to_dict=False)` | **The frontend's read interface.** Opens `DB_PATH`, returns DataFrame (or list of dicts). Prints SQL + re-raises on error. |
| `fetch_resources()` | B2 → local `resources/` (freshest per dir). |
| `ingest_raw_data_from_cloud(sources, queue=None)` | Freshest B2 JSON → `main.<src>.<table>` DuckDB tables. |
| `get_fresh_table_paths(source)` | Resolve freshest B2 `s3://…` path per table/year for a source. |
| `fetch_data_from_sources(years, source, tables, log)` | Run the **extract** path (`Extractor.run`). Admin-triggered. |
| `get_all_tables_by_source()` / `get_table_names` | Table inventory per source. |
| `add_user(username, password)` | bcrypt-hash → upsert `sensitive_seeds/users.csv` → `run_dbt("seed")` → `write_sensitive_seeds()` (push to B2). |
| `run_dbt(action="build"\|"seed", queue=None)` | Invoke dbt with `--full-refresh --target app`. |
| `has_sensitive_seeds_rows()` | True if any sensitive seed CSV has data rows (dev-mode skip check). |

`SECRET_SQL` builds a DuckDB S3 secret from env so `read_json('s3://…')` can reach B2.

## Source ETL (`sources/<src>/`)

A **source** = one upstream provider. Currently only **`s001` = ESPN** (via `espn_api`).

- **`sources/s001/extract.py` → `S001Extractor`**: `SOURCE_NAME="s001"`, `ALL_TRANSFORMERS=[…]`.
  - `_extract(years, classes)` — for each year build an `espn_api.football.League` and hand it to each
    transformer.
  - `run(queue, years, tables)` — extract → `transformer.transform(queue)` → `write_source_data(...)`
    (one B2 JSON file per table/year).
  - `get_table_names()` — `[t.TABLE_NAME for t in ALL_TRANSFORMERS]`.
- **`sources/s001/transformers/<table>.py`** — one file per source table, each a pydantic `…Schema`
  + a `…Transformer(Transformer)` declaring `TABLE_NAME` + `TABLE_SCHEMA` and implementing
  `transform(queue)` (returns list[dict] of rows). The schema is the contract for what lands in B2 →
  `base_s001__<table>`.

| Transformer | `TABLE_NAME` | Schema highlights | → base model |
|---|---|---|---|
| `PlayersTransformer` | `players` | playerId, name, posRank, eligibleSlots, proTeam, position, points (total/avg/projected), percent_owned/started, `stats` list | `base_s001__players` |
| `TeamsTransformer` | `teams` | team_id, names, division, wins/losses/ties, points_for/against, acquisitions, budget, trades, streak, standing, final_standing, owners | `base_s001__teams` |
| `MatchupTransformer` | `matchups` | matchup_week, home/away team+score+projected+lineup, is_playoff, matchup_type. **2018 is special-cased** (uses `scoreboard` not `box_scores`). | `base_s001__matchups` |
| `SettingsTransformer` | `settings` | reg_season_count, matchup_periods, team_count, playoff_team_count, keeper_count, division_map, scoring_format, position_slot_counts | `base_s001__settings` |
| `DraftPickTransformer` | `draftpicks` | team_id, playerId, playerName, round_num, round_pick, bid_amount, keeper_status, nominating_team_id | `base_s001__draftpicks` |

To add a source/table see CLAUDE.md → "Adding a new source"; remember to register in
`SOURCE_EXTRACTOR_MAP` and add the dbt `base_<src>__<table>` + `sources.yml`.

## `backend/utils.py` — shared ETL helpers

- **`Transformer`** (base class): `convert_to_dict(obj)` (reduce to schema fields),
  `apply_schema(obj)` (validate via the pydantic model + append `year`), `transform()` (abstract).
- **`get_s3_client()`** — boto3 client pointed at B2 (env creds).
- **`write_source_data(rows, source, table, year, queue)`** — write rows as JSON to B2 at the source
  path; stamps each row with `meta__source_path` + `meta__date_effective` (these power
  `stg__source_metadata` / `int__source_freshness`).
- **`write_sensitive_seeds()`** — upload `resources/sensitive_seeds/*.csv` to B2 (date-partitioned).
- **`get_date_partition()`** — `YYYY-MM-DD`. Const `NUM_NFL_WEEKS = 18`.

## Cloud storage (Backblaze B2, S3-compatible)

- **Source data:** `data/sources/<source>/<table>/<year>/<date>/<source>_<table>_<year>_<date>.json`
- **Resources:** `resources/<…>/<date>/<file>` (seeds + media), date-partitioned.
- Freshness is "latest date partition wins" — `get_fresh_table_paths` (per table/year) and
  `fetch_resources` (per dir) both select the newest date.

## Env vars (live in git-ignored `.envrc` — never surface values)

- **B2:** `APPLICATION_KEY_ID`, `APPLICATION_KEY`, `ENDPOINT`, `REGION`, `BUCKET_NAME`.
- **ESPN:** `LEAGUE_ID`, `ESPN_S2`, `SWID`.
- **App:** `STORAGE_SECRET` (NiceGUI session).
- **GroupMe:** `ACCESS_TOKEN`, `GROUP_ID`.

## `groupme/app.py` (standalone)

A separate, containerized GroupMe message puller (`run_app()` → writes `output_<GROUP_ID>.json`).
**Not part of the NiceGUI app** — don't wire it into `main.py`.
