# Feature Backlog

Future features we've discussed but not built yet. Lightweight notes — enough to pick the
thread back up later, not full specs. Architecture-level direction lives in
[`architecture-roadmap.md`](architecture-roadmap.md).

Each item has an **`FF-XXX`** id (zero-padded, assigned in order, never reused) so we can
reference it in conversation, branches, and commits.

**Fields** (kept deliberately small — a field only exists if it changes what to do next):
- **Area** — `frontend` / `backend` / `dbt` / `api` / `infra` / `security` / `docs` (multi-valued).
- **Priority** — `Low` / `Med` / `High` (rough; read together with Effort, not alone).
- **Effort** — `S` (< ½ day) / `M` (a day or two) / `L` (multi-day).
- **Status** — `Idea` / `Ready` / `Doing` / `Done` (archive `Done` to the bottom).
- **Done when** — a one-line definition of done, on each item.

## Index

| ID | Title | Area | Priority | Effort | Status |
|----|-------|------|----------|--------|--------|
| FF-001 | Owner-uploaded headshots | frontend, backend | Low | M | Idea |
| FF-002 | Revise sensitive-seed security | security, infra | Low | S–M | Idea |
| FF-003 | Ingest s002 (FantasyData) source | backend, dbt | Low | L | Doing |
| FF-004 | One-command fly.io deploy | infra | Med | M | Idea |
| FF-005 | Fix source-fetch memory crash | backend | Low | M | Idea |
| FF-006 | Owner filter on Player Data table | frontend, dbt | Low | M | Idea |
| FF-007 | Gallery: video upload / display / metadata | frontend, backend | Low | L | Idea |
| FF-008 | Refactor website navigation | frontend | Low | M | Idea |
| FF-009 | Quantify luck via all-play / expected wins | dbt | Low | M | Idea |
| FF-010 | Notification / events dashboard | dbt, backend, frontend | Low | L | Idea |

---

## FF-001 — Owner-uploaded headshots (replace thumbnail)

**Area:** frontend, backend · **Priority:** Low · **Effort:** M · **Status:** Idea

**Done when:** an owner can upload an image that replaces their headshot everywhere, stored
compressed in B2 and surviving a container restart.

**What:** let an owner upload their own image to replace their headshot, instead of the
headshots being a fixed set fetched from B2 at boot.

**Why now-ish:** today headshots are static files (`resources/media/owners/<owner_id>.jpg`)
pulled from B2 by `fetch_resources` and served straight off local disk. Self-service uploads
make the gallery/owner pages feel personal without a maintainer round-trip.

**Pieces it will need:**
- An **upload UI** (likely on the owner's spotlight/gallery page, auth-gated to that owner /
  admin) — NiceGUI `ui.upload`.
- **Storage**: write the uploaded image to B2 (the source of truth), keyed by `owner_id`, so
  it survives container restarts and is picked up by `fetch_resources` on next boot. Decide
  whether to also hot-update the local copy so the change shows immediately.
- **Pre-resize / compress (required as part of this feature):** never store the raw upload at
  full size. On upload, downscale to the display size and compress (e.g. ~128px WebP, ~5–15 KB)
  before writing to B2 — see the headshot sizing discussion in `architecture-roadmap.md`. This
  is the same optimization we'd want even for the current static headshots (they're currently
  211 KB rendered at ~52 px), so doing it here solves both.
- **Validation**: file type/size limits, strip EXIF, enforce square aspect (or center-crop).

**Open questions:** who can change whose image (self-only vs admin override); keep a default
fallback image for owners who never upload; whether to version/overwrite.

---

## FF-002 — Revise sensitive-seed storage security

**Area:** security, infra · **Priority:** Low · **Effort:** S–M · **Status:** Idea

**Done when:** B2-stored seeds are protected beyond bcrypt (least-privilege bucket keys, Fly
secrets, strong `STORAGE_SECRET`, git-history scan) and we've made a deliberate call on
at-rest encryption. (The `STORAGE_SECRET` swap is effectively High priority but trivial — do
it standalone, don't wait on this item.)

**What:** harden how sensitive seeds (`resources/sensitive_seeds/*.csv` — auth password hashes +
owner PII) are stored, especially the copies pushed to B2. Today they're bcrypt-hashed (good) but
stored plaintext-at-rest in B2 under date-partitioned keys.

**Threat model:** a 15-person hobby app — optimize for blast-radius reduction, not APTs. Realistic
risks are a secret leaking (public repo, laptop, image layer) or the B2 bucket/keys being exposed.
bcrypt already means a full `users.csv` leak doesn't directly surrender passwords — that's the
backstop, so none of this is an emergency.

**Easy wins (mostly zero-code, do first):**
- **Least-privilege B2 keys** — scope the application key to the single bucket, read/write only
  (not the account master key). Biggest bang for the buck.
- **Fly secrets, not image-baked env** — set prod secrets via `fly secrets set`, keep them out of
  image layers / `image/.env`.
- **Private bucket + lifecycle rule** to expire old date-partitioned `sensitive_seeds/` uploads
  (otherwise every old `users.csv` lingers forever).
- **Strong `STORAGE_SECRET`** (signs NiceGUI session/auth cookies — a weak one lets an attacker
  forge an authenticated session and bypass login entirely) and **rotate ESPN cookies** periodically.
- **`gitleaks`/`trufflehog` scan of git history** — public repo insurance that no secret/seed was
  ever committed.

**Optional next step (some code):** client-side encrypt the seed CSVs before B2 upload (e.g. Fernet
via `cryptography`, key from a Fly secret like `SEED_ENCRYPTION_KEY`) — encrypt in
`write_sensitive_seeds`, decrypt in `fetch_resources`. Only meaningful because the key lives in a
*different* trust boundary than B2; it hardens the "B2 leaked but app secret didn't" case. Skip if
the key would just sit in the same `.envrc` as the B2 keys.

**Non-goals:** a real secrets manager (Vault/KMS), per-column DB encryption — overkill at this scale.

---

## FF-003 — Ingest s002 (FantasyData) source

**Area:** backend, dbt · **Priority:** Low · **Effort:** L · **Status:** Doing

**Done when:** FantasyData's free prior-year data is in B2 (same partitions as `s001`) and staging
dbt models expose it to downstream models via the existing ids.

**What:** add FantasyData as source `s002`. It's a paid DaaS but the previous year is free — upload
that data to B2 directly (no extractor, to avoid cost) and build staging models so downstream models
can use it. Relevant: <https://fantasydata.com/>.

_Source: GH #12 (in progress)._

---

## FF-004 — One-command fly.io deploy

**Area:** infra · **Priority:** Med · **Effort:** M · **Status:** Idea

**Done when:** a single `make` target builds the container and pushes it to fly.io, after basic
production protection (on `main`, up-to-date).

**What:** a deploy script wrapped in a `make` command that (1) checks the branch is `main` and
up-to-date, (2) builds the docker container, (3) pushes it to fly.io. The roadmap favors staying
local for now (see `architecture-roadmap.md`), but having one-command deploy ready de-risks the
eventual cutover.

_Source: GH #18._

---

## FF-005 — Fix source-fetch memory crash

**Area:** backend · **Priority:** Low · **Effort:** M · **Status:** Idea

**Done when:** fetching any source for any year range completes without OOM (`Error 137`).

**What:** fetching `s001: players` (the largest source) for multiple years crashes the container —
an out-of-memory issue from transforming in-memory before writing to B2. Stream/chunk the transform
so it doesn't hold everything in memory.

_Source: GH #11 (bug)._

---

## FF-006 — Owner filter on Player Data table

**Area:** frontend, dbt · **Priority:** Low · **Effort:** M · **Status:** Idea

**Done when:** the Player Data table can group players by owner, correctly handling mid-season
ownership changes (only counting weeks the owner held the player, with effective weeks shown).

**What:** add an owner filter to the player data table. Non-trivial because ownership can change
within a year — only weeks where the owner actually held the player should count, and the number of
effective weeks should be displayed. Stretch: option to count only weeks the player was started
(not benched).

_Source: GH #27._

---

## FF-007 — Gallery: video upload / display / metadata (Bunny Stream)

**Area:** frontend, backend · **Priority:** Low · **Effort:** L · **Status:** Idea

**Done when:** the Gallery page lets users upload videos to Bunny Stream with metadata, browse them
organized by owner and season, and edit a video's metadata after upload.

**What:** build out the `/gallery` page (currently a "Coming Soon" stub) into a video gallery backed
by Bunny Stream. Sub-pieces (were separate GH issues):
- **Upload** — frontend upload UI + put video to Bunny Stream via the TUS resumable client (no Stream
  endpoint in the bunny SDK). _GH #5._
- **Display** — organize videos by owner and season; link from Splash shotgun counter, Owner History
  spotlight, League Highlights, etc. Stretch: simple thumbs up/down voting. _GH #6._
- **Edit metadata** — an "Edit" button per video calling the TUS/Bunny update API to correct metadata
  after upload. _GH #8._

_Source: GH #7 (parent), #5, #6, #8._

---

## FF-008 — Refactor website navigation

**Area:** frontend · **Priority:** Low · **Effort:** M · **Status:** Idea

**Done when:** every major section is reachable directly from the splash/landing page (not buried
under Stats Center), and the current-season counters take a smaller footprint (compact, or behind a
button) instead of dominating the landing screen.

**What:** rework navigation so the splash page (`/`) is the real hub. Today most of the value lives
under `/stats_center` (Player Data, Draft Analysis, Strength of Schedule, League Highlights, …),
reached via header → Stats Center landing → card → subpage. The splash page itself only shows the
current standings + shotgun-counter tables, which dominate the screen.

**Pieces / ideas:**
- Surface all sections from the splash page (a top-level tile/card grid, like the current Stats Center
  landing but promoted to the front door).
- Shrink the current-season counters (standings, shotgun counter) — compact widgets or tuck them
  behind a button/expander so they don't own the landing page.
- Reconsider whether "Stats Center" stays a separate hub or flattens into the splash nav.
- Keep the header nav (`common_header`) consistent with the new structure.

**Open questions:** flat nav vs keep section hubs; what belongs "above the fold" on the splash;
whether the current counters live on the splash at all or move to their own page.

---

## FF-009 — Quantify luck via all-play / expected wins (deep dive)

**Area:** dbt · **Priority:** Low · **Effort:** M · **Status:** Idea

**Done when:** there's an `int__` model exposing each owner-season's all-play record / expected
wins, and the snub + luck metrics can optionally use it as a more rigorous "you were robbed by
the schedule" measure than today's points-based gate.

**What:** a proper deep dive into quantifying *schedule luck*. Today luck lives in deliberately
small snapshots — median-based `lucky_wins` / `unlucky_losses` (`int__lucky_records`) and the
points-based **Snub / Lucky-in** definition (you missed the playoffs despite outscoring a team
that made it; mirror for lucky-in). Those are intentionally lightweight and we like them for now.

The richer model is **all-play / expected wins**: each week, score every team against the *entire*
league (an all-play record), so a team's expected win% reflects how it would have done versus a
neutral schedule. Then:
- **Expected vs actual wins** = the cleanest "robbed by schedule" measure.
- A more rigorous **snub** = missed the playoffs despite a top-N all-play record (deserved a spot
  on merit, not just on raw points); **lucky-in** = made it despite a poor all-play record.
- Could power a standalone "luck" view, not just the highlight titles.

**Why later:** it's a different stat than points (new intermediate, a different mental model) and
the current snapshots are good enough. This is the "(d)" option from the snub-definition discussion
— captured here so the points-based gate (shipped) can be upgraded deliberately, not rushed.

**Pieces it will need:** an `int__all_play_records` (team-week vs the whole league → weekly all-play
W-L) rolled up to owner-season expected wins; optional wiring into `int__season_titles` to offer an
all-play variant of the snub/luck flags; maybe a dedicated luck mart/page.

---

## FF-010 — Notification / events dashboard (consolidated event feed)

**Area:** dbt, backend, frontend · **Priority:** Low · **Effort:** L · **Status:** Idea

**Done when:** there's a single consolidated **events feed** capturing notable things happening across
the site — at minimum new League-Highlights events and all-time-leaderboard rank changes — in one
queryable place that downstream products can source.

**What:** build a unified stream of "what's going on" across the website, so any number of products can
read from one consolidated event layer instead of each re-deriving "what changed." The dashboard /
consumer surface is undecided on purpose — the value here is the **event-sourcing layer underneath it**.

**First events to emit (League Highlights):**
- A **new highlight event** occurs — e.g. a fresh shotgun, clutch game, best/worst week, a new title
  holder (the same week-grain events we just chip on the spotlight schedule + the season titles).
- An **all-time leaderboard change** — someone enters/moves on an `all_time_records` leaderboard (rank
  change in the All-Time view), e.g. a new career-points leader or a new biggest snub.

**Why build it as a shared layer:** "consolidate the events once, source them many times." Candidate
consumers (none committed yet):
- a **Current Events / activity-feed page** in the app;
- an **iMessage (or GroupMe — see the dormant `groupme/` puller) push hook** to alert the league;
- **context for an LLM-generated news/recap report** (feed the event list to a model → weekly writeup).

**The hard part — detecting "new":** the app **full-refreshes dbt on every boot** (`DbManager.setup`),
so there's no built-in notion of "since last time." An events feed needs **state across runs**: persist a
prior snapshot (e.g. a stored events/leaderboard table in B2, or dbt **snapshots**) and **diff** the new
build against it to materialize *change* events. This is the core design decision; without it we only
have current state, not a stream.

**Pieces it will need:**
- An **event schema / model** (one row per event: type, timestamp/season-week, subject owner(s),
  payload/summary) — likely a new `marts`/`intermediate` layer that unions per-source event producers.
- **Snapshotting + diffing** to turn full-refresh state into append-only events (the state problem above).
- Per-area **event producers** (League Highlights first; later: standings swings, draft, gallery uploads).
- One or more **consumers** (page / push / LLM) — decided later, deliberately out of scope for v1.

**Open questions:** event granularity + schema; where prior state lives (B2 snapshot vs dbt snapshots vs
a small persisted table); de-duplication / "already notified" tracking; which consumer to build first;
whether this wants the eventual FastAPI seam (see `architecture-roadmap.md`) as its read API.
