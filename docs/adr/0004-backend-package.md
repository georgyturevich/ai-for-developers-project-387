# Backend package: FastAPI implementing the contract

## Status

Accepted.

## Context

The repo is currently two packages: the TypeSpec contract at the root and the
React frontend. The frontend only ever talks to a Prism mock of the spec — no
real server enforces the booking rules. The backend needs to serve the contract
and enforce the domain rules server-side, but the domain rules are what make or
break the product and must not be entangled with an HTTP framework.

## Decision

Add a third package, `backend/`, a uv-managed Python 3.14 FastAPI service:

- **Domain core** (`cal_bookings/domain.py`) is pure and framework-free: slot
  grid generation, the Booking Window, past/upcoming boundaries and the
  half-open interval overlap predicate. All rules are functions of their
  arguments; "now" is passed in explicitly and never read from the system clock
  inside the core, so tests freeze time deterministically.
- **Store** (`cal_bookings/store.py`) is an in-memory framework-free store — no
  database, data resets on restart, per the assignment. The overlap check and
  the booking insert are one atomic method with no suspension points, so a
  double-booking race cannot produce two successful bookings on the event loop.
- **HTTP layer** (`cal_bookings/app.py`) is a thin adapter: pydantic models
  mirror the contract shapes exactly (camelCase aliases), routers validate,
  maps every error to the unified error body (`code` + `message`) with the four
  contract codes (`validation_failed`, `duplicate_slug`, `event_type_not_found`,
  `slot_unavailable`), and the framework's default 422/body-parse errors are
  remapped to `400 validation_failed`.
- The Owner timezone (Europe/Moscow) and Business Hours constants already
  fixed by ADR-0003/ADR-0002 are shared by the backend as system constants.

### Test seams

Three seams, exercised by `make backend-test` (which regenerates the spec
first):

1. Domain unit tests with a frozen clock.
2. API integration tests (httpx against the ASGI app).
3. Contract conformance — schemathesis in-process against the generated
   OpenAPI spec with a fresh pre-seeded app; a deliberate response-schema
   drift (e.g. a renamed field) fails the suite.

## Consequences

- The frontend keeps talking to the same contract; switching from the Prism mock
  to the real server is a `VITE_API_URL` change — the backend serves
  `http://localhost:8000` with CORS open for the Vite dev origin.
- Contract edits propagate to the backend via its own compilation of
  `main.tsp` (the root `make` tooling); the backend's spec is gitignored output.
- Domain rules live in exactly one place, the framework-free core, unit-tested
  without any HTTP machinery.
