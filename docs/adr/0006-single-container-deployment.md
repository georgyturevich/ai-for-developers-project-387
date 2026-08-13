# One FastAPI process serves both the SPA and the API on `$PORT`

## Status

Accepted.

## Context

Until now the app only ran as a two-process development topology: a Vite dev
server for the UI and a uvicorn server for the API, wired by a build-time
`VITE_API_URL` and a hardcoded CORS origin. Nothing ran in production: no
Dockerfile existed, nothing read the `PORT` env var, the server bound loopback
only, and the backend could not serve the built frontend at all. The Hexlet
assignment step "Docker и деплой" requires a Dockerfile at the repo root whose
image starts automatically, listens on `$PORT`, and is reachable at a public
URL. The in-memory store (ADR-0004) also carries an architectural constraint:
its Booking overlap check is atomic only on a single event loop, so the
production process must be pinned to one worker and one replica.

## Decision

Ship **one Docker image** containing the entire application: the FastAPI
backend serves both the API and the built SPA from a single process on a single
`$PORT`.

- **Backend change (the only application code change).** `create_app` reads a
  `STATIC_DIR` env var. Unset → today's exact behavior (pure API). Set → a
  `SPAStaticFiles` mount (a small `StaticFiles` subclass with `html=True` plus
  an `index.html` fallback for non-API GET paths) is added *after* the API
  routes, so contract routes always win and keep their JSON `ApiError` 404s.
  The container sets the var to the bundled SPA directory.
- **`$PORT` and bind address.** The image CMD runs the venv's uvicorn with
  `--host 0.0.0.0` and `--port ${PORT:-8000}`. Today nothing reads `$PORT` and
  uvicorn binds loopback-only — both are fixed here; the 8000 fallback keeps a
  bare local `docker run` sane.
- **Exactly one worker, one replica.** ADR-0004's single-event-loop atomicity
  assumption is why the image does not scale beyond this.
- **`VITE_API_URL=""` build-time quirk.** The frontend is built inside the
  image with the env var set to an empty string. The API client's
  `import.meta.env.VITE_API_URL ?? "http://localhost:4010"` fallback keeps the
  empty string, yielding same-origin relative requests. The frontend source
  stays byte-identical — a deliberate, implicit-but-reliable Vite behavior.
- **Hosting: Railway.** `make deploy` runs an attached `railway up`; a `deploy`
  job chained into the release-please workflow deploys every published release
  (release-please is the release source), checking out the tagged revision and
  running `railway up --service <name> --ci` with a project token.

### Alternatives considered and rejected

- **Backend-only image + separate static host.** Two deployables, cross-origin
  CORS, and a baked absolute API URL that breaks on the first domain change.
- **nginx + uvicorn in one container.** Adds a process supervisor just to avoid
  ~15 lines of Python that serve the same files.

## Consequences

- One artifact to build, push, and reason about; the dev loop, backend tests,
  schemathesis conformance, and e2e are untouched because the new behavior is
  env-var-gated.
- The in-memory store resets on every restart and redeploy — accepted for the
  public demo, per the assignment; the README must not promise durable data.
- **Railway sharp edges** a future reader will trip on:
  - `HEALTHCHECK` instructions are ignored; the platform healthcheck path is
    configured in `railway.json` (`GET /event-types`, 200 on an empty store)
    and is deploy-time only, not continuous monitoring.
  - `railway up` uploads the working tree **including uncommitted changes**,
    respects `.gitignore`, and never consults `.dockerignore`.
  - `RAILWAY_TOKEN` accepts **project tokens only** (account tokens are
    rejected); setting both `RAILWAY_TOKEN` and `RAILWAY_API_TOKEN` is an
    error; tokens do not expire — rotation is delete-and-recreate.
  - Non-interactive `railway up` never implicitly creates a project; the empty
    project/service must exist first, and a service gets no public domain
    until `railway domain` generates one.
- The Owner timezone (ADR-0003) is preserved in the container by installing
  system `tzdata` — slim Python base images omit the tz database that
  `ZoneInfo("Europe/Moscow")` needs.
