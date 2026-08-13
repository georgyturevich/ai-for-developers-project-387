## Agent skills

### Issue tracker

Issues live as GitHub issues in this repo, driven through the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical roles map 1:1 to labels of the same name (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Project shape

Three packages, spec-first:

- **Repo root** — the API contract in TypeSpec (`main.tsp`), the single source of truth. `tsp-output/` (OpenAPI spec + bundled docs) is generated output — never hand-edit it; `make` regenerates it, and `npm run mock` serves a Prism mock of the spec on port 4010.
- **`frontend/`** — React + Vite UI that talks to the API only through generated types (`src/api/schema.d.ts`, gitignored). Its `typecheck`/`build` scripts recompile `main.tsp` first, so contract edits propagate automatically. Lint (`oxlint`), tests (Vitest) and typecheck all run inside `frontend/`.
- **`backend/`** — Python 3.14 FastAPI service (uv-managed) implementing the contract. Domain rules live in a framework-free core (`src/cal_bookings/domain.py`) with an injectable clock; data is an in-memory store (resets on restart, per the assignment); all errors use the contract's `code` + `message` body. Lint (`ruff`) and tests (`pytest`, including schemathesis conformance) run inside `backend/`; `make backend-test` regenerates the spec first. The server runs on port 8000 with CORS open for `http://localhost:5173`.
- **E2E** — Playwright at the repo root drives the assembled system (real browser, real Vite dev server, real backend) through the scenarios in `docs/e2e-scenarios.md`; `npm run test:e2e` / `make e2e`. See `docs/agents/` and ADR-0005.

## Deployment

One Docker image (root `Dockerfile`, multi-stage) contains the whole app: the
FastAPI backend serves both the API and the built SPA on a single `$PORT`
(`STATIC_DIR` env var; see ADR-0006). `make deploy` deploys the current working
revision to Railway via an attached `railway up` (uploads uncommitted changes —
`.gitignore` applies, `.dockerignore` does not); every published GitHub release
deploys automatically via a `deploy` job chained into the release-please
workflow (release-please creates releases with `GITHUB_TOKEN`, which GitHub
refuses to use as a trigger for a separate workflow — so the deploy is a second
job in the same run, gated on `release_created`). It uses the `RAILWAY_TOKEN`
secret (a project token, scoped to one project+environment) and the
`RAILWAY_SERVICE` repo variable. Exactly one worker and one replica: the
in-memory store's atomicity assumes a single event loop (ADR-0004).

## Conventional Commits

Binding for every commit an agent makes, and for every PR title and commit
message a maintainer writes. Machine-readable history drives release-please
changelogs (see `.github/workflows/release-please.yml`).

- **Format**: `<type>[(<scope>)]: <subject>` — types are exactly `feat`, `fix`,
  `docs`, `chore`, `refactor`, `test`, `ci`, `build`, `perf`; scope is optional
  and free-form. No other types.
- **Landing paths**: direct pushes need a conventional commit message; squash
  merges need a conventional PR title; merge-commit PRs need every branch commit
  conventional (the merge commit itself is exempt).
- **Enforcement**: none (no commitlint/husky). A non-conventional commit costs a
  missing changelog entry, nothing more.
