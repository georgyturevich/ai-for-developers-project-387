export const OWNER_TIMEZONE = "Europe/Moscow";
export const OWNER_TIMEZONE_LABEL = "МСК";

const dayKeyFormatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: OWNER_TIMEZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

export function dayKeyInOwnerTz(instantIso: string): string {
  return dayKeyFormatter.format(new Date(instantIso));
}

export function ownerTodayKey(now: Date = new Date()): string {
  return dayKeyFormatter.format(now);
}

export const BOOKING_WINDOW_DAYS = 14; // текущий день + 13 следующих

function addDays(dayKey: string, days: number): string {
  const [year, month, day] = dayKey.split("-").map(Number);
  const shifted = new Date(Date.UTC(year, month - 1, day + days));
  const y = shifted.getUTCFullYear();
  const m = String(shifted.getUTCMonth() + 1).padStart(2, "0");
  const d = String(shifted.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function bookingWindowDays(now: Date = new Date()): string[] {
  const today = ownerTodayKey(now);
  return Array.from({ length: BOOKING_WINDOW_DAYS }, (_, i) => addDays(today, i));
}

export function slotEndIso(startIso: string, durationInMinutes: number): string {
  return new Date(new Date(startIso).getTime() + durationInMinutes * 60_000).toISOString();
}

const timeFormatter = new Intl.DateTimeFormat("ru-RU", {
  timeZone: OWNER_TIMEZONE,
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

export function formatTimeRange(startIso: string, durationInMinutes: number): string {
  const start = timeFormatter.format(new Date(startIso));
  const end = timeFormatter.format(new Date(slotEndIso(startIso, durationInMinutes)));
  return `${start}–${end}`;
}

const dayLabelFormatter = new Intl.DateTimeFormat("ru-RU", {
  timeZone: OWNER_TIMEZONE,
  weekday: "short",
  day: "numeric",
  month: "short",
});

export function formatDayLabel(dayKey: string): string {
  // Полдень UTC внутри дня — безопасная точка: при смещении пояса владельца (+3)
  // она гарантированно остаётся в том же календарном дне.
  return dayLabelFormatter.format(new Date(`${dayKey}T12:00:00Z`));
}

export function formatDayAndTimeRange(startIso: string, durationInMinutes: number): string {
  return `${formatDayLabel(dayKeyInOwnerTz(startIso))}, ${formatTimeRange(startIso, durationInMinutes)}`;
}

export function groupByDay<T extends { start: string }>(items: T[]): [string, T[]][] {
  const groups = new Map<string, T[]>();
  for (const item of items) {
    const key = dayKeyInOwnerTz(item.start);
    const group = groups.get(key);
    if (group) {
      group.push(item);
    } else {
      groups.set(key, [item]);
    }
  }
  return [...groups.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, group]) => [
      key,
      group.sort((a, b) => a.start.localeCompare(b.start)),
    ]);
}
