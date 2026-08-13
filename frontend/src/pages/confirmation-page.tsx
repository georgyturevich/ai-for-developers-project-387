import { Link, Navigate, useLocation } from "react-router";
import type { Booking } from "@/api/types";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { OWNER_TIMEZONE_LABEL, formatDayAndTimeRange } from "@/lib/datetime";

// Экран транзиентный: в контракте нет GET /bookings/{id}, поэтому детали
// приходят через router state из ответа POST /bookings. При перезагрузке
// состояние теряется — честно возвращаемся в каталог.
export function ConfirmationPage() {
  const location = useLocation();
  const booking = (location.state as { booking?: Booking } | null)?.booking;

  if (!booking) {
    return <Navigate to="/" replace />;
  }

  return (
    <Card className="mx-auto max-w-lg">
      <CardHeader>
        <CardTitle>Вы записаны</CardTitle>
        <CardDescription>
          Запись подтверждена. Отменить или перенести её нельзя — приходите вовремя.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <dl className="flex flex-col gap-3">
          <div>
            <dt className="text-sm text-muted-foreground">Тип события</dt>
            <dd>{booking.eventType.name}</dd>
          </div>
          <div>
            <dt className="text-sm text-muted-foreground">Время ({OWNER_TIMEZONE_LABEL})</dt>
            <dd>{formatDayAndTimeRange(booking.start, booking.eventType.durationInMinutes)}</dd>
          </div>
          <div>
            <dt className="text-sm text-muted-foreground">Гость</dt>
            <dd>
              {booking.guest.name} · {booking.guest.email}
            </dd>
          </div>
        </dl>
      </CardContent>
      <CardFooter>
        <Link to="/" className={buttonVariants()}>
          К списку типов событий
        </Link>
      </CardFooter>
    </Card>
  );
}
