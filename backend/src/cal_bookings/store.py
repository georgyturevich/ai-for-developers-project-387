"""In-memory store. Framework-free; data resets on restart by design (assignment)."""

from __future__ import annotations

from datetime import datetime, timedelta

from cal_bookings import domain
from cal_bookings.domain import Booking, EventType, OccupiedInterval


class DuplicateSlugError(Exception):
    pass


class SlotUnavailableError(Exception):
    pass


class InMemoryStore:
    def __init__(self) -> None:
        self._event_types: dict[str, EventType] = {}
        self._bookings: list[Booking] = []
        self._next_booking_id = 1

    def create_event_type(self, event_type: EventType) -> None:
        if event_type.id in self._event_types:
            raise DuplicateSlugError(event_type.id)
        self._event_types[event_type.id] = event_type

    def get_event_type(self, slug: str) -> EventType | None:
        return self._event_types.get(slug)

    def list_event_types(self) -> list[EventType]:
        return list(self._event_types.values())

    def occupied_intervals(self) -> list[OccupiedInterval]:
        return [
            OccupiedInterval(
                start=booking.start,
                end=booking.start + timedelta(minutes=booking.duration_in_minutes),
            )
            for booking in self._bookings
        ]

    def create_booking(
        self,
        event_type_id: str,
        start: datetime,
        duration_in_minutes: int,
        guest_name: str,
        guest_email: str,
        guest_comment: str | None,
    ) -> Booking:
        """Check overlap and insert in one call. No awaits anywhere, so atomic on the event loop."""
        end = start + timedelta(minutes=duration_in_minutes)
        for existing in self._bookings:
            existing_end = existing.start + timedelta(minutes=existing.duration_in_minutes)
            if domain.overlaps(existing.start, existing_end, start, end):
                raise SlotUnavailableError
        booking = Booking(
            id=self._next_booking_id,
            event_type_id=event_type_id,
            start=start,
            duration_in_minutes=duration_in_minutes,
            guest_name=guest_name,
            guest_email=guest_email,
            guest_comment=guest_comment,
        )
        self._next_booking_id += 1
        self._bookings.append(booking)
        return booking

    def list_bookings(self) -> list[Booking]:
        return list(self._bookings)
