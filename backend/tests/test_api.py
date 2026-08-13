"""API integration tests: httpx against the ASGI app.

Behavior is asserted on status codes, bodies and error codes only — never on
store internals.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from tests.conftest import EVENT_TYPE, NOW, MutableClock, api_client, api_client_with_clock

# ---------- Ticket 01: skeleton + list Event Types ----------


async def test_fresh_service_lists_no_event_types():
    async with api_client() as client:
        response = await client.get("/event-types")
        assert response.status_code == 200
        assert response.json() == []


async def test_event_types_have_contract_shape():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        response = await client.get("/event-types")
        assert response.json() == [EVENT_TYPE]


# ---------- Ticket 02: create Event Type ----------


async def test_valid_creation_returns_created_event_type():
    async with api_client() as client:
        response = await client.post("/event-types", json=EVENT_TYPE)
        assert response.status_code == 201
        assert response.json() == EVENT_TYPE


async def test_duplicate_slug_conflicts():
    async with api_client() as client:
        assert (await client.post("/event-types", json=EVENT_TYPE)).status_code == 201
        response = await client.post("/event-types", json={**EVENT_TYPE, "name": "Другое"})
        assert response.status_code == 409
        assert response.json() == {"code": "duplicate_slug", "message": response.json()["message"]}
        assert isinstance(response.json()["message"], str)


async def test_bad_slug_pattern_is_validation_failed():
    async with api_client() as client:
        for bad in ["Strizhka", "under_score", "-strizhka", "strizhka-", "стрижка"]:
            response = await client.post("/event-types", json={**EVENT_TYPE, "id": bad})
            assert response.status_code == 400, bad
            assert response.json()["code"] == "validation_failed", bad


async def test_empty_name_is_validation_failed():
    async with api_client() as client:
        response = await client.post("/event-types", json={**EVENT_TYPE, "name": ""})
        assert response.status_code == 400
        assert response.json()["code"] == "validation_failed"


async def test_duration_out_of_range_is_validation_failed():
    async with api_client() as client:
        for duration in [0, -1, 541, 1000]:
            response = await client.post("/event-types", json={**EVENT_TYPE, "durationInMinutes": duration})
            assert response.status_code == 400, duration
            assert response.json()["code"] == "validation_failed"


async def test_missing_fields_are_validation_failed():
    async with api_client() as client:
        for body in [{}, {"id": "x"}, {"id": "x", "name": "n"}, {"id": "x", "name": "n", "description": "d"}]:
            response = await client.post("/event-types", json=body)
            assert response.status_code == 400, body
            assert response.json()["code"] == "validation_failed"


async def test_framework_422_never_leaks():
    async with api_client() as client:
        response = await client.post("/event-types", json={"id": 42, "name": "x", "description": "d", "durationInMinutes": "abc"})
        assert response.status_code == 400
        body = response.json()
        assert set(body) == {"code", "message"}
        assert body["code"] == "validation_failed"


async def test_error_body_is_uniform():
    async with api_client() as client:
        responses = [
            await client.get("/event-types/nope/slots"),
            await client.post("/event-types", json={"id": "bad_id", "name": "", "description": "", "durationInMinutes": 0}),
            await client.post("/bookings", json={}),
        ]
        for response in responses:
            assert response.status_code == 400 or response.status_code == 404
            assert set(response.json()) == {"code", "message"}


# ---------- Ticket 03: list free Slots ----------


async def test_slots_list_across_the_whole_window():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        response = await client.get("/event-types/strizhka/slots")
        assert response.status_code == 200
        slots = response.json()
        assert len(slots) == 14 * 9
        assert slots[0] == {"start": "2026-08-12T06:00:00Z"}
        assert slots[-1] == {"start": "2026-08-25T14:00:00Z"}
        starts = [slot["start"] for slot in slots]
        assert starts == sorted(set(starts))


async def test_slots_never_in_the_past():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        response = await client.get("/event-types/strizhka/slots")
        starts = [slot["start"] for slot in response.json()]
        assert all(start >= "2026-08-12T06:00:00Z" for start in starts)


async def test_unknown_event_type_slots_404():
    async with api_client() as client:
        response = await client.get("/event-types/nope/slots")
        assert response.status_code == 404
        assert response.json() == {"code": "event_type_not_found", "message": response.json()["message"]}


async def test_malformed_slug_in_path_is_validation_failed():
    async with api_client() as client:
        response = await client.get("/event-types/Strizhka/slots")
        assert response.status_code == 400
        assert response.json()["code"] == "validation_failed"


async def test_unparseable_body_is_validation_failed():
    async with api_client() as client:
        response = await client.post("/event-types", content=b"\x00\xff\xfe", headers={"Content-Type": "application/json"})
        assert response.status_code == 400
        assert set(response.json()) == {"code", "message"}
        assert response.json()["code"] == "validation_failed"


# ---------- Ticket 04: create Booking ----------


async def test_valid_booking_returns_full_shape():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        response = await client.post(
            "/bookings",
            json={
                "eventTypeId": "strizhka",
                "start": "2026-08-12T07:00:00Z",
                "guest": {"name": "Иван Петров", "email": "ivan@example.com", "comment": "Заранее"},
            },
        )
        assert response.status_code == 201
        assert response.json() == {
            "id": 1,
            "eventType": {"id": "strizhka", "name": "Стрижка", "durationInMinutes": 60},
            "start": "2026-08-12T07:00:00Z",
            "guest": {"name": "Иван Петров", "email": "ivan@example.com", "comment": "Заранее"},
        }


async def test_booking_ids_increment_from_one():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        first = await client.post("/bookings", json={"eventTypeId": "strizhka", "start": "2026-08-12T07:00:00Z", "guest": {"name": "A", "email": "a@example.com"}})
        second = await client.post("/bookings", json={"eventTypeId": "strizhka", "start": "2026-08-12T08:00:00Z", "guest": {"name": "B", "email": "b@example.com"}})
        assert first.json()["id"] == 1
        assert second.json()["id"] == 2


async def test_off_grid_start_is_validation_failed():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        response = await client.post(
            "/bookings",
            json={"eventTypeId": "strizhka", "start": "2026-08-12T07:30:00Z", "guest": {"name": "A", "email": "a@example.com"}},
        )
        assert response.status_code == 400
        assert response.json()["code"] == "validation_failed"


async def test_past_start_is_validation_failed():
    now = datetime(2026, 8, 12, 10, 0, 0, tzinfo=UTC)
    async with api_client(now=now) as client:
        await client.post("/event-types", json=EVENT_TYPE)
        response = await client.post(
            "/bookings",
            json={"eventTypeId": "strizhka", "start": "2026-08-12T09:00:00Z", "guest": {"name": "A", "email": "a@example.com"}},
        )
        assert response.status_code == 400
        assert response.json()["code"] == "validation_failed"


async def test_outside_window_start_is_validation_failed():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        response = await client.post(
            "/bookings",
            json={"eventTypeId": "strizhka", "start": "2026-08-26T06:00:00Z", "guest": {"name": "A", "email": "a@example.com"}},
        )
        assert response.status_code == 400
        assert response.json()["code"] == "validation_failed"


async def test_booking_unknown_event_type_404():
    async with api_client() as client:
        response = await client.post(
            "/bookings",
            json={"eventTypeId": "nope", "start": "2026-08-12T07:00:00Z", "guest": {"name": "A", "email": "a@example.com"}},
        )
        assert response.status_code == 404
        assert response.json()["code"] == "event_type_not_found"


async def test_invalid_guest_email_is_validation_failed():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        response = await client.post(
            "/bookings",
            json={"eventTypeId": "strizhka", "start": "2026-08-12T07:00:00Z", "guest": {"name": "A", "email": "not-an-email"}},
        )
        assert response.status_code == 400
        assert response.json()["code"] == "validation_failed"


async def test_overlap_is_slot_unavailable():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        await client.post("/bookings", json={"eventTypeId": "strizhka", "start": "2026-08-12T07:00:00Z", "guest": {"name": "A", "email": "a@example.com"}})
        response = await client.post(
            "/bookings",
            json={"eventTypeId": "strizhka", "start": "2026-08-12T07:00:00Z", "guest": {"name": "B", "email": "b@example.com"}},
        )
        assert response.status_code == 409
        assert response.json() == {"code": "slot_unavailable", "message": response.json()["message"]}


async def test_overlap_across_different_event_types_is_slot_unavailable():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        await client.post("/event-types", json={"id": "masazh", "name": "Массаж", "description": "d", "durationInMinutes": 30})
        await client.post("/bookings", json={"eventTypeId": "strizhka", "start": "2026-08-12T07:00:00Z", "guest": {"name": "A", "email": "a@example.com"}})
        response = await client.post(
            "/bookings",
            json={"eventTypeId": "masazh", "start": "2026-08-12T07:00:00Z", "guest": {"name": "B", "email": "b@example.com"}},
        )
        assert response.status_code == 409
        assert response.json()["code"] == "slot_unavailable"


async def test_back_to_back_bookings_are_allowed():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        first = await client.post("/bookings", json={"eventTypeId": "strizhka", "start": "2026-08-12T07:00:00Z", "guest": {"name": "A", "email": "a@example.com"}})
        second = await client.post("/bookings", json={"eventTypeId": "strizhka", "start": "2026-08-12T08:00:00Z", "guest": {"name": "B", "email": "b@example.com"}})
        assert first.status_code == 201
        assert second.status_code == 201


async def test_booked_slot_disappears_from_listing():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        before = await client.get("/event-types/strizhka/slots")
        assert {"start": "2026-08-12T07:00:00Z"} in before.json()
        await client.post("/bookings", json={"eventTypeId": "strizhka", "start": "2026-08-12T07:00:00Z", "guest": {"name": "A", "email": "a@example.com"}})
        after = await client.get("/event-types/strizhka/slots")
        assert {"start": "2026-08-12T07:00:00Z"} not in after.json()
        assert len(after.json()) == len(before.json()) - 1


async def test_double_booking_race_yields_one_success_one_conflict():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        payload = {"eventTypeId": "strizhka", "start": "2026-08-12T07:00:00Z", "guest": {"name": "A", "email": "a@example.com"}}
        first, second = await asyncio.gather(client.post("/bookings", json=payload), client.post("/bookings", json=payload))
        assert sorted([first.status_code, second.status_code]) == [201, 409]


# ---------- Ticket 05: list upcoming Bookings ----------


async def test_fresh_service_lists_no_bookings():
    async with api_client() as client:
        response = await client.get("/bookings")
        assert response.status_code == 200
        assert response.json() == []


async def test_upcoming_bookings_sorted_ascending_across_event_types():
    async with api_client() as client:
        await client.post("/event-types", json=EVENT_TYPE)
        await client.post("/event-types", json={**EVENT_TYPE, "id": "masazh", "name": "Массаж", "durationInMinutes": 30})
        await client.post("/bookings", json={"eventTypeId": "strizhka", "start": "2026-08-12T08:00:00Z", "guest": {"name": "A", "email": "a@example.com"}})
        await client.post("/bookings", json={"eventTypeId": "masazh", "start": "2026-08-12T07:00:00Z", "guest": {"name": "B", "email": "b@example.com"}})
        response = await client.get("/bookings")
        assert response.status_code == 200
        bookings = response.json()
        assert [b["start"] for b in bookings] == ["2026-08-12T07:00:00Z", "2026-08-12T08:00:00Z"]
        assert bookings[0]["eventType"]["id"] == "masazh"
        assert bookings[1]["eventType"]["id"] == "strizhka"


async def test_ongoing_booking_shown_ended_booking_hidden():
    clock = MutableClock(NOW)
    async with api_client_with_clock(clock) as client:
        await client.post("/event-types", json=EVENT_TYPE)
        await client.post("/bookings", json={"eventTypeId": "strizhka", "start": "2026-08-12T07:00:00Z", "guest": {"name": "A", "email": "a@example.com"}})

        clock.value = datetime(2026, 8, 12, 7, 30, 0, tzinfo=UTC)  # 07:30Z: ongoing
        shown = await client.get("/bookings")
        assert [b["start"] for b in shown.json()] == ["2026-08-12T07:00:00Z"]

        clock.value = datetime(2026, 8, 12, 8, 0, 0, tzinfo=UTC)  # 08:00Z: ended (end == now)
        hidden = await client.get("/bookings")
        assert hidden.json() == []
