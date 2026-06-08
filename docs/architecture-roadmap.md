# Architecture Roadmap — Frontend/Backend Evolution

> Strategic notes (not an active work item). Captures the long-term plan for where this
> project's frontend and backend are headed, and *why*, so the reasoning survives between
> sessions. Nothing here is urgent — see "Current stance" at the bottom.

## The core insight: the data layer is the durable asset

The heart of this app is **dbt + DuckDB**, and the project already enforces the discipline
that *all analytics are precomputed in marts and the frontend only issues thin `SELECT`s*
(see `CLAUDE.md`). That discipline means **the marts are effectively an API contract.** The
frontend is a disposable veneer over them.

Consequences that drive every decision below:

- Everything built in dbt carries over **100%** to any future frontend. The NiceGUI page
  code is the only throwaway part, and by design it's thin.
- A future frontend port is **re-skinning, not re-architecting**. That collapses the cost of
  "prototype in Python now, port later" to almost nothing — there is no penalty for staying
  in NiceGUI while it's productive.

## Why not Rust (the question that kicked this off)

The instinct "Python isn't the best frontend language, maybe Rust" conflates two things:

- For a **frontend**, the real alternative to Python is **TypeScript/JavaScript**, not Rust.
  "Rust on the frontend" means WASM (Leptos/Yew/Dioxus) — a young, small-ecosystem niche, and
  the one place Claude is *weakest*. Since the plan is to lean on Claude for the frontend,
  Rust actively undercuts that. The charting/component/dashboard ecosystem lives in TS.
- For the **backend**, it's ESPN ingestion + serving thin SELECTs for ~15 users. Rust buys
  performance we will never need and costs the seamless dbt/DuckDB/Python integration and our
  own fluency. DuckDB is already native C++ under the hood. **Keep the backend Python.** Learn
  Rust only for its own sake, never for this project's needs.

## Target stack (the destination, agreed)

- **Frontend:** Next.js + TypeScript + Tailwind + shadcn/ui + a charting lib (Recharts / visx).
- **Backend:** FastAPI serving JSON from DuckDB (the "seam", below), with dbt/DuckDB unchanged.
- **Hosting:** Fly.io (two apps), *eventually* — staying local for now to avoid monthly cost.

This is squarely Claude's strongest zone, and reviewing TS/React is far more approachable for
a Python dev than Rust would ever be.

## The "seam" — a thin FastAPI JSON layer

**What it is:** a handful of FastAPI routes, each wrapping a query we already have, that turn
*"run this SELECT, hand back the rows"* into *"`GET /api/...` → JSON."*

**Why it's needed:** today a NiceGUI page calls `DbManager.query(...)` **in-process** — a
direct Python call that only works because the frontend *is* Python in the same process. A
React app runs in the **browser**, a separate program with no `DbManager`; the only thing it
can do is make an HTTP request and get JSON back. The seam is that boundary.

```python
# api.py — FastAPI is ALREADY running under NiceGUI; this just adds routes
@app.get("/api/all_time_records")
def all_time_records(section: str):
    return DbManager.query(
        f"select * from main_marts.all_time_records "
        f"where section = '{section}' order by category, metric_label, rank",
        to_dict=True,
    )
```

Three things to notice:

1. **No logic moves or changes** — the SQL is identical, it just relocates from inside a page
   function to behind a URL.
2. **It's tiny** because the marts already do the work; most endpoints are one `DbManager.query`.
3. **It decouples the two sides** — the backend stops caring *who* asks (NiceGUI, React, curl),
   which is what enables a page-by-page migration with no flag day.

**Mental model:** it's the same pattern we already trust, one layer up. dbt marts are the
contract between *dbt* and *the app*; the seam is the contract between *the app's data* and
*any frontend*.

**Caveat:** the `/api/` routes need the same auth gating `AuthMiddleware` does today — don't
leave the JSON open.

## Repo structure (monorepo)

**Decision: monorepo.** "Deploy separately" (a runtime property — two Fly apps, two
Dockerfiles) is *not* the same as "repo separately" (a source-control property). Independent
deploys come free from a monorepo; splitting into two repos buys nothing here and costs real
friction (cross-repo PRs, hand-syncing the API contract, two CI configs). Monorepo is correct
well beyond this project's size — it's not a starter-tier compromise.

Destination layout (reached *incrementally*, not up front):

```
fantasy-footballer/
  backend/                      # Python — data layer + the seam
    src/fantasy_footballer/
      api/                      # FastAPI routes (the seam)
      backend/                  # DbManager, sources/, ingestion
    dbt/fantasy_footballer/     # marts live with the backend that serves them
    resources/                  # gitignored DuckDB + seeds
    pyproject.toml
    Dockerfile
    Makefile
  frontend/                     # TypeScript — Next.js app
    src/
    package.json
    Dockerfile
  fly.backend.toml
  fly.frontend.toml
  Makefile                      # root: orchestrates both
  README.md
```

Conventions:

1. **One directory per deployable unit, each fully self-contained** (own Dockerfile, own
   dependency manifest, own toolchain). `dbt/` lives under `backend/` because `DbManager`
   runs dbt at boot and serves its marts — it's not a third independent thing.
2. **Don't share a runtime across the boundary** — `backend/` has a Poetry venv, `frontend/`
   has `node_modules`; they meet only over HTTP/JSON.
3. **Root holds orchestration, not code** — a root Makefile + shared `.gitignore`/CI.
4. **Resist heavy monorepo tooling** (Nx/Turborepo/Bazel) — overkill for one person and two
   deployables. A Makefile and two Dockerfiles is the right amount of machinery.
5. **Generated contract (the monorepo superpower):** FastAPI auto-emits an OpenAPI schema;
   one CI codegen step turns it into TypeScript types so a renamed mart column breaks the
   frontend *compile* until fixed. (Deferred topic — see below.)

## Deployment shape

Two Fly apps from one repo, each pointing at its dir's Dockerfile. Frontend → backend over
HTTP: prefer **same-origin** (frontend proxies `/api/*` to the backend) to avoid CORS
entirely. Not happening until the project is pushed far locally first.

## Migration path (incremental, low-risk)

1. **Now:** keep `src/fantasy_footballer/{backend,frontend,...}` as is; NiceGUI is productive.
2. **Seam step:** add `src/fantasy_footballer/api/` (FastAPI routes). Still one package, one
   deploy. NiceGUI untouched.
3. **React step:** add `frontend/` (Next.js) at the repo root. NiceGUI and React coexist, both
   reading the same `/api/`.
4. **Cutover:** as React pages replace NiceGUI pages, delete the NiceGUI modules one at a time.
5. **Tidy (optional, cosmetic):** move the Python under `backend/` for symmetry once the last
   NiceGUI page is gone. The "big restructure" is really a rename at the very end, after the
   risky UI migration is already proven.

## When to start (the trigger)

Stay in NiceGUI until its UX ceiling actually bites — when you want polish / charts /
interactions that Quasar fights you on (the "ugly to the human eye" friction is the leading
indicator). Don't port ASAP; don't big-bang rewrite.

## Current stance

- **Push the project far locally before any Fly.io deploy**, to avoid the monthly cloud cost.
  There is no production environment and no users yet — local dev is the whole world for now.
- Keep building features in NiceGUI; keep *all* display logic in marts and pages thin so the
  eventual port stays cheap.

## Deferred learning topic

**OpenAPI → TypeScript type generation** — how the generated-contract flow actually works
(FastAPI's OpenAPI schema → codegen → TS types consumed by the React app). Flagged for a
dedicated future session; it's the most outside the owner's current wheelhouse.
