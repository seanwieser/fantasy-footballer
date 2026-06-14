# Backend map

How data gets into the DuckDB warehouse and how the app talks to it. Counterparts:
[`dbt/fantasy_footballer/MODELS.md`](../../../dbt/fantasy_footballer/MODELS.md) (analytics) and
[`frontend/FRONTEND.md`](../frontend/FRONTEND.md) (pages).

**Keep it current:** if you add/remove a `DbManager` method, change the boot path, add a source or
transformer, or change the cloud-storage layout / env vars, update this file in the same change.

## The key mental model: two separate data paths

These are easy to confuse — they move data in opposite directions and run at different times.

1. **Extract (source → B2)** — *write* path. For `s001` (ESPN) it's **admin-triggered**:
   `DbManager.fetch_data_from_sources` → `S001Extractor.run`, pulling via `espn_api` (code in
   `sources/`). For `s003` (iMessage) it's **local-only** and **lives outside the deployed package**
   in `scripts/imessage/` — run by the owner via `make extract-imessage[-full]` (`python3 -m imessage`),
   reading the local `chat.db`; it can't run on a server, so its code/deps aren't shipped in the image.
   Both validate through pydantic and write raw JSON to B2. **Not part of normal boot.**
2. **Ingest + build (B2 → DuckDB → marts)** — *read/assemble* path, runs at every boot. Downloads the
   B2 JSON, `CREATE OR REPLACE TABLE`s it into DuckDB, then runs dbt. Code: `db.py`. Each source's
   `INGEST_MODE` decides which slices are loaded: **`snapshot`** (s001) takes the freshest file per
   table/year; **`append`** (s003) unions *every* uploaded slice and lets dbt dedupe.

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
| `ingest_raw_data_from_cloud(sources, queue=None)` | B2 JSON → `main.<src>.<table>` DuckDB tables. Dispatches on the source's `INGEST_MODE` (snapshot vs append). |
| `get_fresh_table_paths(source)` | Resolve freshest B2 `s3://…` path per table/year (snapshot sources, e.g. s001). |
| `get_all_table_paths(source)` | Resolve **every** B2 `s3://…` path per table (append sources, e.g. s003) — all slices unioned. |
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

### `s003` = the league iMessage group chat (local-only, lives in `scripts/imessage/`)

`s003` is split so nothing local-only ships in the deployed image:

- **Deployed (in `src/`):** `backend/sources/s003/source.py` → **`S003Source`** — a lightweight ingest
  descriptor (`SOURCE_NAME="s003"`, `INGEST_MODE="append"`, `get_table_names()` → `[messages,
  reactions]`). This is what `SOURCE_EXTRACTOR_MAP` points at; its `run()` just raises (guard against an
  accidental `/admin` trigger). No bs4/sqlite imports.
- **Local-only (in `scripts/imessage/`, NOT deployed):** the extractor + parser + transformers + the
  `python3 -m imessage` entry. Extraction runs **on the owner's machine** (needs the local `chat.db`,
  the `imessage-exporter` binary, Full Disk Access, and the optional bs4 dep — `poetry install --with
  imessage`), driven by `make extract-imessage` (incremental) / `make extract-imessage-full` (first run).

`scripts/imessage/extract.py::run(queue, full)`:
  1. **Snapshot + prune** — `.backup` `chat.db` to a gitignored temp copy (read-only on the source),
     then on the copy drop Apple's triggers and `delete` every non-target row from `chat`,
     `chat_message_join`, **and `message`** (resolved by `display_name = IMESSAGE_GROUP_NAME`). Pruning
     `message` is essential: otherwise the exporter dumps all other threads into `orphaned.html`.
     `imessage-exporter -t` is a *union* participant filter and can't target one thread, so we prune
     instead and export the copy with `-p`.
  2. **Incremental window** — `_latest_b2_extract_date()` reads B2; re-export from `(latest − 1 day)`
     to today (or full history if `--full` / no prior slices).
  3. **DB attribution** — `_build_db_maps()` reads the pruned copy to map each message GUID → `handle.id`
     (raw phone/email) → `owner_id` (sentinel `-1` if unmapped; `is_from_me` → the `Me` id). Reactions
     come from here too — tapbacks are `message` rows (`associated_message_type` 2000-2007 add /
     3000-3007 remove, `associated_message_guid` → reacted-to message); each (message, reactor) collapses
     to its latest live tapback. Attribution is **not** taken from the HTML sender (a contact name).
  4. **Export + parse + write** — `imessage-exporter -p <copy> -f html -c disabled` → `parse_html_export`
     (mirrors the 4.x askama templates; `orphaned.html` skipped) yields message rows, owner attached via
     the GUID map. `--full` calls `purge_cloud()` first (wipes B2 `s003`) for a clean rebuild. Then group
     rows by message-year, validate via the transformers, `write_source_data` one B2 slice per year per table.

`scripts/imessage/transformers/{messages,reactions}.py` — `MessageSchema`/`MessagesTransformer`
(`messages`) and `ReactionSchema`/`ReactionsTransformer` (`reactions`):

| Transformer | `TABLE_NAME` | Schema highlights | → base model |
|---|---|---|---|
| `MessagesTransformer` | `messages` | message_uid, owner_id (sender), sent_at, text, word/char_count, has_attachment/attachment_count, service, thread_name | `base_s003__messages` |
| `ReactionsTransformer` | `reactions` | reaction_uid, message_uid, reactor_owner_id, reaction_type | `base_s003__reactions` |

**Attribution map (local, never uploaded):** `resources/local/owner_handles.csv` —
columns `handle,owner_id`, one row per league member's `handle.id` (raw phone/email, exact match)
**plus a `Me` row** for the owner's own sent messages. Used only at extract time to attribute
senders/reactors → owners (resolution is local so **B2 stores `owner_id`, never raw handles**; even a
hashed phone number is reversible, so a wrong/missing handle is fixed by editing the CSV and re-running
`make extract-imessage-full`). It is **not** a dbt seed and **not** a participant filter. It lives in
**`resources/local/`** — the never-synced directory — rather than `sensitive_seeds/`, so neither
`write_sensitive_seeds()` (push) nor `fetch_resources()` (boot pull) ever touch it: the deployed app
never reads it (only the local extract does), so phone numbers stay strictly on the owner's machine.
Owner identity → `owner_name` is attached downstream in dbt via the existing `owner_names` seed. Back it
up wherever you keep local secrets — not B2.

> **Directory convention:** `resources/sensitive_seeds/` = sensitive dbt seeds that **sync to B2** and
> load at boot; `resources/local/` = sensitive files that are **machine-local, never synced** (not dbt
> seeds). The directory boundary *is* the sync policy — put a new never-uploaded file in `resources/local/`.

**Privacy:** raw `text` reaches B2 + `base_s003__messages`/`stg__chat_messages` only; every model
from `int__owner_chat_activity` onward is owner-grain counts. Needs league consent before the first
extract (per CLAUDE.md / the backlog).

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
  `fetch_resources` (per dir) both select the newest date. **Append sources (s003)** are the
  exception: `get_all_table_paths` ingests *every* slice (the incremental windows overlap by a day)
  and `base_s003__*` dedupe on the uids.

## Env vars (live in git-ignored `.envrc` — never surface values)

- **B2:** `APPLICATION_KEY_ID`, `APPLICATION_KEY`, `ENDPOINT`, `REGION`, `BUCKET_NAME`.
- **ESPN:** `LEAGUE_ID`, `ESPN_S2`, `SWID`.
- **iMessage (s003, local extract only):** `IMESSAGE_GROUP_NAME` (target chat display name; defaults
  to `Sco Chos Ep.11`), `IMESSAGE_DB_PATH` (optional; defaults to `~/Library/Messages/chat.db`).
- **App:** `STORAGE_SECRET` (NiceGUI session).
- **GroupMe:** `ACCESS_TOKEN`, `GROUP_ID`.

## `groupme/app.py` (standalone)

A separate, containerized GroupMe message puller (`run_app()` → writes `output_<GROUP_ID>.json`).
**Not part of the NiceGUI app** — don't wire it into `main.py`.
