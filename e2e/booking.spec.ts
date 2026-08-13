import { expect, test, type Page } from "@playwright/test";
import { dayKeyInOwnerTz, formatDayLabel, formatTimeRange } from "../frontend/src/lib/datetime";

const BACKEND_URL = "http://localhost:8000";
const FRONTEND_URL = "http://localhost:5173";

const SLOT_BUTTON = /^\d{2}:\d{2}–\d{2}:\d{2}$/;

const EVENT_DURATION = 60;

let seedCounter = 0;

function uniqueSlug(prefix: string): string {
  seedCounter += 1;
  return `${prefix}-${Date.now()}-${seedCounter}`;
}

function uniqueGuest(prefix: string) {
  return {
    name: `Гость ${prefix} ${Date.now()}`,
    email: `${prefix}-${Date.now()}@example.com`,
    comment: "Комментарий от гостя.",
  };
}

function eventTypeName(slug: string): string {
  return `Тип события ${slug}`;
}

async function createEventTypeViaApi(slug: string, durationInMinutes = EVENT_DURATION): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/event-types`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: slug,
      name: eventTypeName(slug),
      description: "Тип события, созданный e2e-сценарием через публичный API.",
      durationInMinutes,
    }),
  });
  expect(response.status).toBe(201);
}

// Opens the catalog and the seeded Event Type through the UI.
async function openEventTypeFromCatalog(page: Page, slug: string): Promise<void> {
  await page.goto(`${FRONTEND_URL}/`);
  await expect(page.getByText("На что можно записаться")).toBeVisible();
  const card = page.locator('[data-slot="card"]').filter({ hasText: eventTypeName(slug) });
  await expect(card).toBeVisible();
  await card.getByRole("link", { name: "Выбрать" }).click();
  await expect(page.getByRole("heading", { name: eventTypeName(slug) })).toBeVisible();
}

// Books the first offered free Slot through the UI and lands on the
// confirmation screen. Returns the booked Slot start (UTC ISO).
async function bookFirstFreeSlot(
  page: Page,
  guest: { name: string; email: string; comment: string },
): Promise<string> {
  const slotButton = page.getByRole("button", { name: SLOT_BUTTON }).first();
  await slotButton.click();
  await page.getByRole("button", { name: "Продолжить" }).click();

  const startIso = new URL(page.url()).searchParams.get("start");
  expect(startIso).toBeTruthy();

  await page.getByLabel("Имя").fill(guest.name);
  await page.getByLabel("Email").fill(guest.email);
  await page.getByLabel("Комментарий").fill(guest.comment);
  await page.getByRole("button", { name: "Записаться" }).click();

  await expect(page.getByText("Вы записаны")).toBeVisible();
  return startIso as string;
}

test.describe("e2e scenarios (docs/e2e-scenarios.md)", () => {
  test("S1 — Guest books a Slot", async ({ page }) => {
    const slug = uniqueSlug("s1");
    const guest = uniqueGuest("s1");

    await createEventTypeViaApi(slug);
    await openEventTypeFromCatalog(page, slug);

    await bookFirstFreeSlot(page, guest);

    await expect(page.getByText("Запись подтверждена. Отменить или перенести её нельзя")).toBeVisible();
    await expect(page.getByText(eventTypeName(slug))).toBeVisible();
    await expect(page.getByText(guest.name)).toBeVisible();
    await expect(page.getByText(guest.email)).toBeVisible();
  });

  test("S2 — a booked Slot is no longer offered", async ({ page }) => {
    const slug = uniqueSlug("s2");
    const guest = { ...uniqueGuest("s2"), comment: "" };

    await createEventTypeViaApi(slug);
    await openEventTypeFromCatalog(page, slug);

    const bookedStart = await bookFirstFreeSlot(page, guest);

    await page.goto(`${FRONTEND_URL}/types/${slug}`);
    const dayLabel = formatDayLabel(dayKeyInOwnerTz(bookedStart));
    const timeLabel = formatTimeRange(bookedStart, EVENT_DURATION);

    const bookedDay = page.getByRole("button", { name: dayLabel });
    await expect(bookedDay).toBeVisible();

    if (await bookedDay.isDisabled()) {
      // The whole day offers no Slots any more — the booked one included.
      await expect(page.getByText("На этот день свободных слотов нет.")).toBeVisible();
    } else {
      await bookedDay.click();
      await expect(page.getByRole("button", { name: timeLabel, exact: true })).toHaveCount(0);
    }
  });

  test("S3 — a Booking appears in the Owner Area", async ({ page }) => {
    const slug = uniqueSlug("s3");
    const guest = { ...uniqueGuest("s3"), comment: "Хочу обсудить детали." };

    await createEventTypeViaApi(slug);
    await openEventTypeFromCatalog(page, slug);
    await bookFirstFreeSlot(page, guest);

    await page.getByRole("link", { name: "Владельцу" }).click();
    await expect(page.getByRole("heading", { name: "Предстоящие записи" })).toBeVisible();

    const bookingCard = page.locator('[data-slot="card"]').filter({ hasText: guest.email });
    await expect(bookingCard).toBeVisible();
    await expect(bookingCard).toContainText(eventTypeName(slug));
    await expect(bookingCard).toContainText(guest.name);
  });

  test("S4 — the Owner creates an Event Type through the Owner Area", async ({ page }) => {
    const slug = uniqueSlug("s4");

    await page.goto(`${FRONTEND_URL}/`);
    await expect(page.getByText("На что можно записаться")).toBeVisible();
    await page.getByRole("link", { name: "Владельцу" }).click();
    await expect(page.getByRole("heading", { name: "Предстоящие записи" })).toBeVisible();

    await page.getByRole("link", { name: "Создать тип события" }).click();
    await page.getByLabel("Адрес (slug)").fill(slug);
    await page.getByLabel("Название").fill(eventTypeName(slug));
    await page.getByLabel("Описание").fill("Тип события, созданный через кабинет владельца.");
    await page.getByLabel("Длительность, минут").fill(String(EVENT_DURATION));
    await page.getByRole("button", { name: "Создать тип события" }).click();

    await expect(page.getByText("На что можно записаться")).toBeVisible();
    const card = page.locator('[data-slot="card"]').filter({ hasText: eventTypeName(slug) });
    await expect(card).toBeVisible();
    await expect(card).toContainText(`${EVENT_DURATION} мин`);
  });
});
