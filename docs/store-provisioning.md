# Provisioning the retrieval store

The retrieval lane searches a persisted local vector store built from `corpus/`.
That store (`chroma_db/`) is a **build artifact**: it is git-ignored and must be
built once per environment before the app serves traffic. `retrieval.answer()`
reads it; it never builds it, and — per issue #8 — **the app never triggers
ingestion in the request path.**

## One-command bootstrap (local / CI)

```bash
make bootstrap          # pip install -r requirements.txt + python ingest.py --if-missing
# or:
scripts/build_store.sh  # same thing; add --force to rebuild
```

`python ingest.py` flags:

| Command | Behaviour |
|---|---|
| `python ingest.py` | build from scratch (default) |
| `python ingest.py --if-missing` | build only if no non-empty store exists (idempotent — safe to run on every deploy) |
| `python ingest.py --force` | always rebuild |

`ingest.store_exists()` reports whether a non-empty store is present, so a build
step can decide without rebuilding.

## Deploying with the app (Render)

The store must exist in the same filesystem the web service reads from. Build it
in the service's **build/pre-deploy step**, not at request time. When Lane 4 adds
the Streamlit web service to `render.yaml`, add the store build to its
`buildCommand`:

```yaml
services:
  - name: live-answer-card            # Lane 4 owns this service block
    type: web
    runtime: python
    buildCommand: pip install -r requirements.txt && python ingest.py --if-missing
    startCommand: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: FAST_MODEL_PROVIDER
        sync: false                    # real keys set in the Render dashboard, never committed
      - key: FAST_MODEL_NAME
        sync: false
      - key: FAST_MODEL_BASE_URL
        sync: false
      - key: FAST_MODEL_API_KEY
        sync: false
```

This snippet is a **template**, not wired into `render.yaml` yet: `app.py` is
still in flight on Lane 4, and the PRD flags that whether the required Render
surface is a **Workflow** or a plain **web service** is unconfirmed
(`ignore-gameplan.context/issue_0_PRD.md`). Two shapes work:

- **Build step (recommended, simplest):** the `buildCommand` above builds the
  store into the same container the web service runs, every deploy. `--if-missing`
  keeps redeploys fast.
- **Render Workflow + shared disk:** a standalone job runs `python ingest.py` and
  writes `chroma_db/` to a persistent disk that the web service also mounts.
  Heavier; only needed if ingestion must run separately from the web build.

The existing `render.yaml` (the static landing page) is untouched by this.

## First build cost

The first build downloads the embedding model (~80 MB) and writes ~80 chunks;
subsequent `--if-missing` runs are near-instant. Build embeds locally with no API
key. Model keys (`FAST_MODEL_*`) are only needed to polish keyword phrasing at
runtime; without them retrieval falls back to grounded, heading-derived keywords.
