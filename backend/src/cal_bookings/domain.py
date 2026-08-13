"""Pure, framework-free domain core.

Slot grid generation, the Booking Window, past/upcoming boundaries and the
half-open interval overlap predicate. Everything here is a pure function of its
inputs — "now" is always passed in explicitly so tests can freeze it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

OWNER_TIMEZONE = ZoneInfo("Europe/Moscow")

BUSINESS_HOURS_END = time(hour=18)

WINDOW_LENGTH_DAYS = 14  # the current day plus the next 13

GRID_ANCHOR = time(hour=9)


@dataclass(frozen=True)
class EventType:
    id: str
    name: str
    description: str
    duration_in_minutes: int


@dataclass(frozen=True)
class OccupiedInterval:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class Booking:
    id: int
    event_type_id: str
    start: datetime
    duration_in_minutes: int
    guest_name: str
    guest_email: str
    guest_comment: str | None


def window_start_date(now: datetime) -> date:
    return now.astimezone(OWNER_TIMEZONE).date()


def window_dates(now: datetime) -> list[date]:
    start = window_start_date(now)
    return [start + timedelta(days=i) for i in range(WINDOW_LENGTH_DAYS)]


def day_anchor_utc(day: date) -> datetime:
    """09:00 in the Owner's timezone on `day`, as a UTC instant."""
    local = datetime.combine(day, GRID_ANCHOR, tzinfo=OWNER_TIMEZONE)
    return local.astimezone(UTC)


def day_end_utc(day: date) -> datetime:
    """18:00 in the Owner's timezone on `day`, as a UTC instant."""
    local = datetime.combine(day, BUSINESS_HOURS_END, tzinfo=OWNER_TIMEZONE)
    return local.astimezone(UTC)


def grid_offsets(duration_minutes: int) -> list[timedelta]:
    """Start offsets from the 09:00 anchor for slots that fit within Business Hours."""
    step = timedelta(minutes=duration_minutes)
    day_length = day_end_utc(date.min) - day_anchor_utc(date.min)
    offsets: list[timedelta] = []
    offset = timedelta(0)
    while offset + step <= day_length:
        offsets.append(offset)
        offset += step
    return offsets


def day_grid_starts(day: date, duration_minutes: int) -> list[datetime]:
    anchor = day_anchor_utc(day)
    return [anchor + offset for offset in grid_offsets(duration_minutes)]


def is_valid_grid_start(start: datetime, duration_minutes: int) -> bool:
    """True when `start` is on the 09:00-anchored grid and its slot fits in Business Hours."""
    day = start.astimezone(OWNER_TIMEZONE).date()
    anchor = day_anchor_utc(day)
    if start < anchor:
        return False
    if start + timedelta(minutes=duration_minutes) > day_end_utc(day):
        return False
    return (start - anchor) % timedelta(minutes=duration_minutes) == timedelta(0)


def is_within_window(start: datetime, now: datetime) -> bool:
    """True when `start` falls on a calendar day inside the Booking Window."""
    start_day = start.astimezone(OWNER_TIMEZONE).date()
    last_day = window_start_date(now) + timedelta(days=WINDOW_LENGTH_DAYS - 1)
    return window_start_date(now) <= start_day <= last_day


def is_past(start: datetime, now: datetime) -> bool:
    return start < now


def is_upcoming(end: datetime, now: datetime) -> bool:
    return end > now


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Half-open interval predicate: touching boundaries do not overlap."""
    return a_start < b_end and b_start < a_end


def generate_slot_starts(
    event_type: EventType, now: datetime, occupied: list[OccupiedInterval] | None = None
) -> list[datetime]:
    """Free Slot starts across the whole Booking Window, ascending."""
    occupied = occupied or []
    duration = event_type.duration_in_minutes
    free: list[datetime] = []
    for day in window_dates(now):
        for start in day_grid_starts(day, duration):
            if is_past(start, now):
                continue
            end = start + timedelta(minutes=duration)
            if any(overlaps(interval.start, interval.end, start, end) for interval in occupied):
                continue
            free.append(start)
    return free
