import { Link } from "react-router";
import { useUpcomingBookings } from "@/api/queries";
import { PageError } from "@/components/page-error";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { OWNER_TIMEZONE_LABEL, formatDayLabel, formatTimeRange, groupByDay } from "@/lib/datetime";

export function OwnerBookingsPage() {
  const query = useUpcomingBookings();

  if (query.isPending) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (query.isError) {
    return <PageError onRetry={() => query.refetch()} />;
  }

  const grouped = groupByDay(query.data);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold">Предстоящие записи</h1>
          <p className="text-sm text-muted-foreground">
            по московскому времени ({OWNER_TIMEZONE_LABEL})
          </p>
        </div>
        <Link to="/owner/event-types/new" className={buttonVariants({ variant: "outline" })}>
          Создать тип события
        </Link>
      </div>

      {grouped.length === 0 ? (
        <p className="py-16 text-center text-muted-foreground">Предстоящих записей нет.</p>
      ) : (
        grouped.map(([day, bookings]) => (
          <section key={day} className="flex flex-col gap-3">
            <h2 className="flex items-center gap-2 text-lg font-medium">
              {formatDayLabel(day)}
              <Badge variant="secondary">{bookings.length}</Badge>
            </h2>
            <div className="grid gap-3">
              {bookings.map((booking) => (
                <Card key={booking.id}>
                  <CardContent className="flex flex-col gap-1">
                    <p className="font-medium">
                      {formatTimeRange(booking.start, booking.eventType.durationInMinutes)} —{" "}
                      {booking.eventType.name}
                    </p>
                    <p>
                      {booking.guest.name} ·{" "}
                      <a className="text-primary hover:underline" href={`mailto:${booking.guest.email}`}>
                        {booking.guest.email}
                      </a>
                    </p>
                    {booking.guest.comment ? (
                      <p className="text-sm text-muted-foreground">{booking.guest.comment}</p>
                    ) : null}
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}
