import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { API_ERROR_CODES, ContractError } from "@/api/errors";
import { useEventTypes, useSlots } from "@/api/queries";
import { PageError } from "@/components/page-error";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { NotFoundPage } from "@/pages/not-found-page";
import {
  OWNER_TIMEZONE_LABEL,
  bookingWindowDays,
  formatDayLabel,
  formatTimeRange,
  groupByDay,
  ownerTodayKey,
} from "@/lib/datetime";

export function SlotsPage() {
  const { eventTypeId } = useParams<{ eventTypeId: string }>();
  const navigate = useNavigate();
  const eventTypesQuery = useEventTypes();
  const slotsQuery = useSlots(eventTypeId ?? "");

  const groupedSlots = useMemo(
    () => groupByDay(slotsQuery.data ?? []),
    [slotsQuery.data],
  );

  // Лента дней — окно записи. Дни из ответа сервера добавляем тоже:
  // против настоящего бэкенда это одно и то же множество, а Prism-мок
  // отдаёт статичные примеры, которые иначе могли бы «выпасть» из ленты.
  const days = useMemo(() => {
    const slotDays = groupedSlots.map(([day]) => day);
    return [...new Set([...bookingWindowDays(), ...slotDays])].sort();
  }, [groupedSlots]);

  const [selectedDay, setSelectedDay] = useState<string | null>(null);
  const [selectedStart, setSelectedStart] = useState<string | null>(null);

  if (eventTypesQuery.isPending || slotsQuery.isPending) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const eventType = eventTypesQuery.data?.find((item) => item.id === eventTypeId);
  const slotsNotFound =
    slotsQuery.error instanceof ContractError &&
    slotsQuery.error.code === API_ERROR_CODES.eventTypeNotFound;

  if (slotsNotFound || (eventTypesQuery.isSuccess && !eventType)) {
    return <NotFoundPage title="Тип события не найден" />;
  }

  if (eventTypesQuery.isError) {
    return <PageError onRetry={() => eventTypesQuery.refetch()} />;
  }

  if (slotsQuery.isError) {
    return <PageError onRetry={() => slotsQuery.refetch()} />;
  }

  const slotsByDay = new Map(groupedSlots);
  const currentDay =
    selectedDay && days.includes(selectedDay)
      ? selectedDay
      : (groupedSlots[0]?.[0] ?? ownerTodayKey());
  const daySlots = slotsByDay.get(currentDay) ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">{eventType.name}</h1>
        <p className="text-muted-foreground">{eventType.description}</p>
        <div>
          <Badge variant="secondary">{eventType.durationInMinutes} мин</Badge>
        </div>
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">Выберите день</h2>
        <div className="flex flex-wrap gap-2">
          {days.map((day) => (
            <Button
              key={day}
              variant={day === currentDay ? "default" : "outline"}
              disabled={!slotsByDay.has(day)}
              onClick={() => {
                setSelectedDay(day);
                setSelectedStart(null);
              }}
            >
              {formatDayLabel(day)}
            </Button>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">
          Выберите время{" "}
          <span className="text-sm font-normal text-muted-foreground">
            по московскому времени ({OWNER_TIMEZONE_LABEL})
          </span>
        </h2>
        {daySlots.length === 0 ? (
          <p className="text-muted-foreground">На этот день свободных слотов нет.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {daySlots.map((slot) => (
              <Button
                key={slot.start}
                variant={slot.start === selectedStart ? "default" : "outline"}
                onClick={() => setSelectedStart(slot.start)}
              >
                {formatTimeRange(slot.start, eventType.durationInMinutes)}
              </Button>
            ))}
          </div>
        )}
      </section>

      <div>
        <Button
          size="lg"
          disabled={selectedStart === null}
          onClick={() =>
            navigate(`/types/${eventType.id}/book?start=${encodeURIComponent(selectedStart ?? "")}`)
          }
        >
          Продолжить
        </Button>
      </div>
    </div>
  );
}
