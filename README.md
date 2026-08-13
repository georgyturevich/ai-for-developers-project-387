# Calendar Bookings

### Hexlet tests and linter status:
[![Actions Status](https://github.com/georgyturevich/ai-for-developers-project-386/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/georgyturevich/ai-for-developers-project-386/actions)

## Demo

The public deployment: <https://cal-bookings-production.up.railway.app>

Browse Event Types and book a Slot as a Guest; open the Owner Area at `/owner`
to manage Event Types and view upcoming Bookings. Data lives in an in-memory
store, so it resets on every redeploy — this is a demo, not a durable service
(see ADR-0004).

## Deployment

One Docker image (`Dockerfile`, multi-stage) contains the whole app: the
FastAPI backend serves both the API and the built SPA on a single `$PORT`
(see ADR-0006). `make deploy` deploys the current working revision to Railway;
every published GitHub release deploys automatically.

## Commits

The repository follows [Conventional Commits](https://www.conventionalcommits.org):
commit messages and PR titles are `<type>[(<scope>)]: <subject>` with types from
`feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`, `perf`.
Direct pushes need a conventional commit message; squash merges need a
conventional PR title; merge-commit PRs need every branch commit conventional.
The convention is documented for agents in `AGENTS.md`.
