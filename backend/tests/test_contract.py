"""Contract conformance: schemathesis in-process against the generated OpenAPI spec.

Every operation from main.tsp is exercised; any response that violates the
generated schema (including an undeclared 5xx) fails the suite. A fresh,
pre-seeded app instance is used for every generated request, so runs are
isolated and the state-dependent success paths are reachable.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import schemathesis

from cal_bookings import domain
from cal_bookings.app import create_app

SPEC = Path(__file__).parents[2] / "tsp-output" / "@typespec" / "openapi3" / "openapi.yaml"

SEEDED_SLUG = "strizhka"

# The app under test gets a frozen clock (ADR-0004), so the suite is
# deterministic at any wall-clock moment — the seeded start must simply lie on
# the 60-minute grid inside the Booking Window relative to this instant.
FROZEN_NOW = datetime(2026, 8, 12, 6, 0, tzinfo=UTC)


def _future_seeded_start() -> str:
    """The day after the frozen instant, 09:00 in the Owner timezone."""
    tomorrow = FROZEN_NOW.astimezone(domain.OWNER_TIMEZONE).date() + timedelta(days=1)
    return domain.day_anchor_utc(tomorrow).isoformat()


schema = schemathesis.openapi.from_path(str(SPEC))


@schemathesis.hook("before_call")
def _pin_state_dependent_parameters(context, case, kwargs) -> None:
    if case.operation.path == "/event-types/{eventTypeId}/slots":
        case.path_parameters["eventTypeId"] = SEEDED_SLUG
    elif case.operation.path == "/bookings" and case.operation.method.upper() == "POST" and isinstance(case.body, dict):
        case.body["eventTypeId"] = SEEDED_SLUG
        case.body["start"] = _future_seeded_start()
        # Pin the Guest to a plain value: the backend's EmailStr accepts
        # internationalized addresses that the contract's `email` format rejects,
        # so generated exotic addresses would be echoed back in a 201 that then
        # violates the response schema.
        case.body["guest"] = {
            "name": "Иван Петров",
            "email": "ivan.petrov@example.com",
            "comment": "Хочу обсудить детали заранее.",
        }


@schema.parametrize()
def test_contract_conformance(case) -> None:
    app = create_app(clock=lambda: FROZEN_NOW)
    app.state.store.create_event_type(
        domain.EventType(id=SEEDED_SLUG, name="Стрижка", description="Тестовый тип события.", duration_in_minutes=60)
    )
    case.operation.app = app
    case.call_and_validate()
