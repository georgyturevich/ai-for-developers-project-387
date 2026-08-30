"""Domain unit tests: the pure core, driven with a fixed clock.

Now = 2026-08-12T06:00Z == 09:00 MSK on Wednesday 12 Aug 2026.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from itertools import pairwise

from cal_bookings import domain
from cal_bookings.domain import EventType, OccupiedInterval
from tests.conftest import NOW


def _group_by_day(starts: list[datetime]) -> dict[date, list[datetime]]:
    groups: dict[date, list[datetime]] = {}
    for start in starts:
        groups.setdefault(start.astimezone(domain.OWNER_TIMEZONE).date(), []).append(start)
    return groups


def event_type(duration: int = 60) -> EventType:
    return EventType(id="strizhka", name="Стрижка", description="x", duration_in_minutes=duration)


# ---------- Grid ----------


def test_anchor_and_day_end_are_moscow_0900_1800():
    assert domain.day_anchor_utc(date(2026, 8, 12)) == datetime(2026, 8, 12, 6, 0, tzinfo=UTC)
    assert domain.day_end_utc(date(2026, 8, 12)) == datetime(2026, 8, 12, 15, 0, tzinfo=UTC)


def test_thirty_minute_grid_has_seventeen_offsets_for_sixty_minute_duration():
    offsets = domain.grid_offsets(60)
    assert len(offsets) == 17
    assert offsets[1] - offsets[0] == timedelta(minutes=30)
    assert all(b - a == timedelta(minutes=30) for a, b in pairwise(offsets))


def test_540_minute_grid_has_exactly_one_slot():
    assert domain.grid_offsets(540) == [timedelta(0)]


def test_ninety_minute_grid_steps_every_thirty_minutes():
    offsets = domain.grid_offsets(90)
    assert len(offsets) == 16
    assert offsets[-1] + timedelta(minutes=90) == timedelta(hours=9)
    assert all(b - a == timedelta(minutes=30) for a, b in pairwise(offsets))


def test_grid_start_on_anchor_is_valid():
    assert domain.is_valid_grid_start(datetime(2026, 8, 12, 6, 0, tzinfo=UTC), 60)


def test_half_hour_start_is_valid_for_sixty_minute_duration():
    assert domain.is_valid_grid_start(datetime(2026, 8, 12, 6, 30, tzinfo=UTC), 60)


def test_grid_start_mid_step_is_invalid():
    assert not domain.is_valid_grid_start(datetime(2026, 8, 12, 6, 15, tzinfo=UTC), 60)
    assert not domain.is_valid_grid_start(datetime(2026, 8, 12, 6, 15, tzinfo=UTC), 45)


def test_grid_start_before_anchor_is_invalid():
    assert not domain.is_valid_grid_start(datetime(2026, 8, 12, 5, 0, tzinfo=UTC), 60)


def test_grid_start_not_fitting_in_day_is_invalid():
    assert not domain.is_valid_grid_start(datetime(2026, 8, 12, 15, 0, tzinfo=UTC), 60)
    assert not domain.is_valid_grid_start(datetime(2026, 8, 12, 14, 30, tzinfo=UTC), 60)
    assert not domain.is_valid_grid_start(datetime(2026, 8, 12, 14, 30, tzinfo=UTC), 45)


def test_540_minute_slot_is_valid():
    assert domain.is_valid_grid_start(datetime(2026, 8, 12, 6, 0, tzinfo=UTC), 540)


# ---------- Booking Window ----------


def test_window_is_today_plus_thirteen_days():
    days = domain.window_dates(NOW)
    assert days[0] == date(2026, 8, 12)
    assert days[-1] == date(2026, 8, 25)
    assert len(days) == 14


def test_window_boundaries():
    inside = datetime(2026, 8, 25, 15, 0, tzinfo=UTC)  # 18:00 MSK Aug 25
    outside = datetime(2026, 8, 26, 6, 0, tzinfo=UTC)  # 09:00 MSK Aug 26
    assert domain.is_within_window(inside, NOW)
    assert not domain.is_within_window(outside, NOW)
    assert not domain.is_within_window(datetime(2026, 8, 11, 6, 0, tzinfo=UTC), NOW)


# ---------- Past / upcoming ----------


def test_past_boundary():
    assert not domain.is_past(datetime(2026, 8, 12, 6, 0, tzinfo=UTC), NOW)
    assert domain.is_past(datetime(2026, 8, 12, 5, 59, tzinfo=UTC), NOW)


def test_upcoming_boundary():
    end = datetime(2026, 8, 12, 8, 0, tzinfo=UTC)
    assert not domain.is_upcoming(end, end)  # end == now -> not upcoming
    assert domain.is_upcoming(end, end - timedelta(seconds=1))


# ---------- Slot generation ----------


def test_sixty_minute_slots_step_every_thirty_minutes_across_whole_window():
    starts = domain.generate_slot_starts(event_type(60), NOW)
    assert len(starts) == 14 * 17
    assert starts[0] == NOW
    assert starts[-1] == datetime(2026, 8, 25, 14, 0, tzinfo=UTC)
    for day_starts in _group_by_day(starts).values():
        assert len(day_starts) == 17
        assert all(b - a == timedelta(minutes=30) for a, b in pairwise(day_starts))


def test_slots_past_now_are_excluded():
    now = datetime(2026, 8, 12, 10, 0, tzinfo=UTC)  # 13:00 MSK
    starts = domain.generate_slot_starts(event_type(60), now)
    assert starts[0] == now
    assert all(start >= now for start in starts)
    assert len(starts) == 9 + 13 * 17  # 9 left today + 13 full days


def test_forty_five_minute_type_stays_on_half_hour_grid():
    starts = domain.generate_slot_starts(event_type(45), NOW)
    for day_starts in _group_by_day(starts).values():
        assert len(day_starts) == 17
        assert all(b - a == timedelta(minutes=30) for a, b in pairwise(day_starts))
        anchor = domain.day_anchor_utc(day_starts[0].astimezone(domain.OWNER_TIMEZONE).date())
        assert all((s - anchor) % timedelta(minutes=30) == timedelta(0) for s in day_starts)


def test_non_multiple_of_thirty_duration_last_start_fits_business_hours():
    starts = domain.generate_slot_starts(event_type(45), NOW)
    for day_starts in _group_by_day(starts).values():
        last = day_starts[-1]
        assert last + timedelta(minutes=45) <= domain.day_end_utc(last.astimezone(domain.OWNER_TIMEZONE).date())


def test_slot_starting_exactly_now_is_offered():
    now = datetime(2026, 8, 12, 7, 0, tzinfo=UTC)
    starts = domain.generate_slot_starts(event_type(60), now)
    assert starts[0] == now


def test_540_minute_event_type_has_one_slot_per_day():
    starts = domain.generate_slot_starts(event_type(540), NOW)
    assert len(starts) == 14
    assert all(s.hour == 6 for s in starts)


def test_occupied_slot_disappears():
    occupied = [OccupiedInterval(datetime(2026, 8, 12, 7, 0, tzinfo=UTC), datetime(2026, 8, 12, 8, 0, tzinfo=UTC))]
    starts = domain.generate_slot_starts(event_type(60), NOW, occupied)
    for hidden in [datetime(2026, 8, 12, 6, 30, tzinfo=UTC), datetime(2026, 8, 12, 7, 0, tzinfo=UTC), datetime(2026, 8, 12, 7, 30, tzinfo=UTC)]:
        assert hidden not in starts
    assert len(starts) == 14 * 17 - 3


# ---------- Overlap matrix ----------


def _overlaps(a: float, a_len: float, b: float, b_len: float) -> bool:
    base = datetime(2026, 8, 12, tzinfo=UTC)
    return domain.overlaps(
        base + timedelta(hours=a),
        base + timedelta(hours=a + a_len),
        base + timedelta(hours=b),
        base + timedelta(hours=b + b_len),
    )


def test_touching_intervals_do_not_overlap():
    assert not _overlaps(7, 1, 8, 1)
    assert not _overlaps(8, 1, 7, 1)


def test_partial_overlap_is_overlap():
    assert _overlaps(7, 1, 7.5, 1)
    assert _overlaps(7.5, 1, 7, 1)


def test_containment_is_overlap():
    assert _overlaps(7, 2, 7.5, 0.5)


def test_identical_intervals_overlap():
    assert _overlaps(7, 1, 7, 1)


def test_disjoint_intervals_do_not_overlap():
    assert not _overlaps(7, 1, 9, 1)
