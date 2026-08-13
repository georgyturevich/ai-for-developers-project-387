import { describe, expect, test } from "vitest";
import { bookingFormSchema, eventTypeFormSchema } from "./schemas";

describe("bookingFormSchema", () => {
  test("accepts a complete guest form", () => {
    const result = bookingFormSchema.safeParse({
      name: "Иван Петров",
      email: "ivan.petrov@example.com",
      comment: "Хочу обсудить детали заранее.",
    });
    expect(result.success).toBe(true);
  });

  test("rejects an empty name", () => {
    const result = bookingFormSchema.safeParse({ name: "", email: "ivan@example.com" });
    expect(result.success).toBe(false);
  });

  test("rejects a malformed email", () => {
    const result = bookingFormSchema.safeParse({ name: "Иван", email: "ivan@" });
    expect(result.success).toBe(false);
  });

  test("comment is optional", () => {
    const result = bookingFormSchema.safeParse({ name: "Иван", email: "ivan@example.com" });
    expect(result.success).toBe(true);
  });
});

describe("eventTypeFormSchema", () => {
  const validEventType = {
    id: "strizhka",
    name: "Стрижка",
    description: "Стрижка и укладка за один час.",
    durationInMinutes: 60,
  };

  test("accepts a valid event type", () => {
    expect(eventTypeFormSchema.safeParse(validEventType).success).toBe(true);
  });

  test("description may be empty — the contract requires the field but allows \"\"", () => {
    expect(eventTypeFormSchema.safeParse({ ...validEventType, description: "" }).success).toBe(true);
  });

  test.each(["Стрижка", "Strizhka", "-strizhka", "strizhka-", "strizhka--2", "stri zhka", ""])(
    "rejects slug %j — pattern ^[a-z0-9]+(-[a-z0-9]+)*$",
    (id) => {
      expect(eventTypeFormSchema.safeParse({ ...validEventType, id }).success).toBe(false);
    },
  );

  test.each(["a", "a1", "strizhka-2", "a-b-c"])("accepts slug %j", (id) => {
    expect(eventTypeFormSchema.safeParse({ ...validEventType, id }).success).toBe(true);
  });

  test.each([0, -5, 541, 30.5])("rejects duration %s — must be an integer 1–540", (durationInMinutes) => {
    expect(eventTypeFormSchema.safeParse({ ...validEventType, durationInMinutes }).success).toBe(false);
  });

  test.each([1, 540])("accepts boundary duration %s", (durationInMinutes) => {
    expect(eventTypeFormSchema.safeParse({ ...validEventType, durationInMinutes }).success).toBe(true);
  });

  test("coerces a numeric string from a number input", () => {
    const result = eventTypeFormSchema.safeParse({ ...validEventType, durationInMinutes: "45" });
    expect(result.success).toBe(true);
    expect(result.data?.durationInMinutes).toBe(45);
  });

  test("rejects an empty name", () => {
    expect(eventTypeFormSchema.safeParse({ ...validEventType, name: "" }).success).toBe(false);
  });
});
