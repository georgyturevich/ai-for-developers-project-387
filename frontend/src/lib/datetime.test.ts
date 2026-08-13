import { describe, expect, test } from "vitest";
import {
  bookingWindowDays,
  dayKeyInOwnerTz,
  formatDayLabel,
  formatTimeRange,
  groupByDay,
  ownerTodayKey,
  slotEndIso,
} from "./datetime";

describe("dayKeyInOwnerTz", () => {
  test("instant after midnight in owner tz belongs to the new owner day", () => {
    // 2026-08-11 21:30 UTC = 2026-08-12 00:30 в Europe/Moscow (UTC+3)
    expect(dayKeyInOwnerTz("2026-08-11T21:30:00Z")).toBe("2026-08-12");
  });

  test("morning instant stays on the same owner day", () => {
    // 2026-08-11 06:00 UTC = 2026-08-11 09:00 в Europe/Moscow
    expect(dayKeyInOwnerTz("2026-08-11T06:00:00Z")).toBe("2026-08-11");
  });
});

describe("ownerTodayKey", () => {
  test("uses the owner day, not the UTC day", () => {
    // 2026-08-11 22:00 UTC — в поясе владельца уже 01:00 12 августа
    expect(ownerTodayKey(new Date("2026-08-11T22:00:00Z"))).toBe("2026-08-12");
  });
});

describe("bookingWindowDays", () => {
  test("returns the current owner day plus the next 13 days", () => {
    // 2026-08-11 10:00 UTC = 13:00 MSK — «сегодня» владельца 11 августа
    const days = bookingWindowDays(new Date("2026-08-11T10:00:00Z"));
    expect(days).toEqual([
      "2026-08-11",
      "2026-08-12",
      "2026-08-13",
      "2026-08-14",
      "2026-08-15",
      "2026-08-16",
      "2026-08-17",
      "2026-08-18",
      "2026-08-19",
      "2026-08-20",
      "2026-08-21",
      "2026-08-22",
      "2026-08-23",
      "2026-08-24",
    ]);
  });

  test("window rolls over a month boundary", () => {
    const days = bookingWindowDays(new Date("2026-08-30T12:00:00Z"));
    expect(days.at(0)).toBe("2026-08-30");
    expect(days.at(-1)).toBe("2026-09-12");
    expect(days).toHaveLength(14);
  });
});

describe("slotEndIso", () => {
  test("end = start + duration", () => {
    expect(slotEndIso("2026-08-12T06:00:00Z", 60)).toBe("2026-08-12T07:00:00.000Z");
  });
});

describe("formatTimeRange", () => {
  test("renders start and derived end in the owner timezone", () => {
    // 06:00 UTC = 09:00 MSK
    expect(formatTimeRange("2026-08-12T06:00:00Z", 30)).toBe("09:00–09:30");
  });

  test("max duration fills the whole business day 09:00–18:00", () => {
    expect(formatTimeRange("2026-08-12T06:00:00Z", 540)).toBe("09:00–18:00");
  });
});

describe("formatDayLabel", () => {
  test("renders weekday and date in Russian", () => {
    expect(formatDayLabel("2026-08-12")).toBe("ср, 12 авг.");
  });

  test("Saturday renders for a weekend day key", () => {
    expect(formatDayLabel("2026-08-15")).toBe("сб, 15 авг.");
  });
});

describe("groupByDay", () => {
  test("groups by owner day and sorts days and items ascending", () => {
    const slots = [
      { start: "2026-08-13T07:00:00Z" }, // 10:00 MSK 13 авг
      { start: "2026-08-12T06:00:00Z" }, // 09:00 MSK 12 авг
      { start: "2026-08-12T15:00:00Z" }, // 18:00 MSK 12 авг — позже по времени
      { start: "2026-08-12T21:30:00Z" }, // 00:30 MSK 13 авг — следующий день владельца
    ];
    expect(groupByDay(slots)).toEqual([
      [
        "2026-08-12",
        [{ start: "2026-08-12T06:00:00Z" }, { start: "2026-08-12T15:00:00Z" }],
      ],
      [
        "2026-08-13",
        [{ start: "2026-08-12T21:30:00Z" }, { start: "2026-08-13T07:00:00Z" }],
      ],
    ]);
  });

  test("empty input gives empty output", () => {
    expect(groupByDay([])).toEqual([]);
  });
});
