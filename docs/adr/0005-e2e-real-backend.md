# End-to-end tests run against the real backend, not the Prism mock

## Status

Accepted.

## Context

The backend is conformance-tested against the contract (schemathesis over the
generated OpenAPI spec) and the frontend is unit-tested, but nothing verifies
that the two work together: the Guest's booking journey and the Owner's flows
have never been exercised in a real browser against the real server. The
frontend normally talks to a Prism mock of the spec — fast and deterministic,
but it cannot prove frontend–backend integration.

## Decision

The e2e suite runs the fully assembled system over real HTTP: a real browser, the
real Vite dev server and the real FastAPI backend with its in-memory store. No
new seams are introduced — the servers start through their existing entry points
and test data enters through the public API, exactly as real Guests and the real
Owner Area would create it.

- **Wall-clock dependence**: the backend clock is only injectable in-process, so
  over HTTP the suite runs on wall-clock time. This is kept safe by the Booking
  Window (the current day plus the next 13, in the Owner's timezone per
  ADR-0003) and by always selecting the first offered free Slot rather than a
  hardcoded time.
- **Seeding**: each scenario seeds its own Event Type through the public API with
  a unique slug, so scenarios are independent and individually rerunnable. The
  Owner Area creation flow itself is exercised as the thing under test in S4.
- **No Prism**: the mock remains available for frontend-only development, but it
  plays no part in the e2e suite.

## Consequences

- Integration regressions are caught where they actually happen — across the
  HTTP boundary between the two packages — rather than mocked away.
- The suite has a wall-clock dependence and is not instant; the Booking Window
  and first-free-Slot selection keep it stable at any time of day.
- Scenario data enters through the public API, which doubles as a live check that
  the Owner and Guest operations the scenarios rely on actually work.
