import "@typespec/http";

using TypeSpec.Http;

@service(#{ title: "Calendar Bookings API" })
@doc("""
  API бронирования слотов для единственного владельца календаря.

  Две роли: владелец (один предопределённый профиль) и анонимные гости.
  Регистрации и аутентификации нет — операции владельца открыты по условию задачи.

  Ключевые доменные правила:
  - Слоты генерируются внутри фиксированных рабочих часов 09:00–18:00 в поясе владельца.
  - Сетка стартов (Slot Grid): якорь 09:00, фиксированный шаг 30 минут независимо от длительности типа события; слот помещается в рабочие часы целиком.
  - Окно записи: текущая дата + 13 следующих дней (пояс владельца); слоты в прошлом не предлагаются.
  - На одно и то же время нельзя создать две записи: запрещено любое пересечение интервалов, даже для разных типов событий.
  """)
namespace CalendarBookings;

// ---------- Scalars ----------

@doc("""
  Идентификатор-слаг, задаваемый владельцем: строчные буквы, цифры и дефисы.
  Максимум 100 символов.
  """)
@pattern("^[a-z0-9]+(-[a-z0-9]+)*$")
@maxLength(100)
@example("strizhka")
scalar Slug extends string;

@doc("Длительность в минутах. Верхняя граница 540 = 9 часов рабочего дня: слот должен целиком помещаться в 09:00–18:00.")
@minValue(1)
@maxValue(540)
@example(60)
scalar Duration extends int32;

// ---------- Models ----------

@doc("Тип события: вид брони, который создаёт владелец. Редактирование и удаление не поддерживаются.")
model EventType {
  @doc("Уникальный идентификатор, задаваемый владельцем при создании.")
  id: Slug;

  @doc("Название, видимое гостю. Максимум 200 символов.")
  @minLength(1)
  @maxLength(200)
  @example("Стрижка")
  name: string;

  @doc("Описание, видимое гостю. Максимум 2000 символов.")
  @maxLength(2000)
  @example("Стрижка и укладка за один час.")
  description: string;

  @doc("Длительность слота этого типа в минутах.")
  durationInMinutes: Duration;
}

@doc("Краткая карточка типа события, вложенная в бронирование.")
model EventTypeSummary {
  id: Slug;

  @doc("Название типа события. Максимум 200 символов.")
  @maxLength(200)
  @example("Стрижка")
  name: string;

  durationInMinutes: Duration;
}

@doc("Свободный слот на сетке Slot Grid (фиксированный шаг 30 минут, якорь 09:00 в поясе владельца). Конец слота выводится: start + длительность типа события.")
model Slot {
  @doc("Начало слота (момент времени в UTC).")
  @example(utcDateTime.fromISO("2026-08-12T06:00:00Z"))
  start: utcDateTime;
}

@doc("Данные гостя, создающего бронирование.")
model GuestInfo {
  @doc("Имя гостя. Максимум 200 символов.")
  @minLength(1)
  @maxLength(200)
  @example("Иван Петров")
  name: string;

  @doc("Email гостя. Максимум 320 символов.")
  @format("email")
  @maxLength(320)
  @example("ivan.petrov@example.com")
  email: string;

  @doc("Комментарий гостя. Максимум 2000 символов.")
  @maxLength(2000)
  @example("Хочу обсудить детали заранее.")
  comment?: string;
}

@doc("Бронирование: резервация слота гостем. Отмена и перенос не поддерживаются.")
model Booking {
  @doc("Серверный идентификатор.")
  @example(1)
  id: int64;

  @doc("Тип события, вложен для самодостаточности списка владельца.")
  eventType: EventTypeSummary;

  @doc("Начало бронирования (UTC). Конец = start + длительность типа.")
  @example(utcDateTime.fromISO("2026-08-13T09:00:00Z"))
  start: utcDateTime;

  guest: GuestInfo;
}

@doc("Тело запроса на создание бронирования.")
model CreateBookingRequest {
  @doc("Тип события, к которому относится слот.")
  eventTypeId: Slug;

  @doc("Выбранный старт слота (UTC). Должен лежать на сетке, внутри окна записи и не в прошлом.")
  @example(utcDateTime.fromISO("2026-08-12T06:00:00Z"))
  start: utcDateTime;

  guest: GuestInfo;
}

// ---------- Errors ----------

@doc("Единое тело ошибки.")
model ApiError {
  @doc("Машиночитаемый код: \"validation_failed\", \"event_type_not_found\", \"duplicate_slug\", \"slot_unavailable\".")
  @example("slot_unavailable")
  code: string;

  @doc("Человекочитаемое описание.")
  @example("Слот занят: время пересекается с существующей записью.")
  message: string;
}

model BadRequest {
  @statusCode statusCode: 400;
  @body body: ApiError;
}

model NotFound {
  @statusCode statusCode: 404;
  @body body: ApiError;
}

model Conflict {
  @statusCode statusCode: 409;
  @body body: ApiError;
}

// ---------- Owner operations ----------

@tag("Owner")
@route("/event-types")
@post
@doc("Владелец: создать тип события. 400 — нарушена валидация (в т.ч. длительность вне 1–540). 409 — slug уже занят.")
op createEventType(@body body: EventType): {
  @statusCode statusCode: 201;
  @body body: EventType;
} | BadRequest | Conflict;

@tag("Owner")
@route("/bookings")
@get
@doc("Владелец: предстоящие встречи — все будущие бронирования всех типов событий одним списком, по возрастанию времени начала. Прошедшие не возвращаются.")
op listUpcomingBookings(): {
  @statusCode statusCode: 200;
  @body body: Booking[];
};

// ---------- Guest operations ----------

@tag("Guest")
@route("/event-types")
@get
@doc("Гость: страница видов брони — все типы событий с названием, описанием и длительностью.")
op listEventTypes(): {
  @statusCode statusCode: 200;
  @body body: EventType[];
};

@tag("Guest")
@route("/event-types/{eventTypeId}/slots")
@get
@doc("""
  Гость: свободные слоты типа события на всё окно записи.
  Возвращаются только свободные старты: если слота нет в списке — он занят, в прошлом или вне правил генерации.
  404 — неизвестный тип события.
  """)
op listSlots(@path eventTypeId: Slug): {
  @statusCode statusCode: 200;
  @body body: Slot[];
} | NotFound;

@tag("Guest")
@route("/bookings")
@post
@doc("""
  Гость: создать бронирование на выбранный слот.
  400 — старт не на сетке, вне окна записи или в прошлом.
  404 — неизвестный тип события.
  409 — слот занят: интервал пересекается с существующей записью любого типа.
  """)
op createBooking(@body body: CreateBookingRequest): {
  @statusCode statusCode: 201;
  @body body: Booking;
} | BadRequest | NotFound | Conflict;
