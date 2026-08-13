import { z } from "zod";

export const bookingFormSchema = z.object({
  name: z.string().min(1, "Укажите имя"),
  email: z.email("Укажите корректный email"),
  comment: z.string().optional(),
});

export type BookingFormValues = z.infer<typeof bookingFormSchema>;

// Паттерн и границы дублируют инварианты контракта (Slug, Duration в main.tsp) —
// фронт валидирует до отправки, сервер остаётся источником истины.
export const SLUG_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

export const eventTypeFormSchema = z.object({
  id: z
    .string()
    .regex(SLUG_PATTERN, "Только строчные латинские буквы, цифры и дефисы между ними"),
  name: z.string().min(1, "Укажите название"),
  description: z.string(),
  durationInMinutes: z.coerce
    .number<number>("Укажите длительность числом")
    .int("Длительность должна быть целым числом минут")
    .min(1, "Минимум 1 минута")
    .max(540, "Максимум 540 минут — слот должен помещаться в 09:00–18:00"),
});

export type EventTypeFormValues = z.infer<typeof eventTypeFormSchema>;
