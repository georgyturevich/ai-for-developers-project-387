import { Link } from "react-router";
import { useEventTypes } from "@/api/queries";
import { PageError } from "@/components/page-error";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function CatalogPage() {
  const query = useEventTypes();

  if (query.isPending) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (query.isError) {
    return <PageError onRetry={() => query.refetch()} />;
  }

  const eventTypes = query.data;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">На что можно записаться</h1>
      {eventTypes.length === 0 ? (
        <p className="py-16 text-center text-muted-foreground">
          Типов событий пока нет — загляните позже.
        </p>
      ) : (
        <div className="grid gap-4">
          {eventTypes.map((eventType) => (
            <Card key={eventType.id}>
              <CardHeader>
                <CardTitle>{eventType.name}</CardTitle>
                <CardDescription>{eventType.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Badge variant="secondary">{eventType.durationInMinutes} мин</Badge>
              </CardContent>
              <CardFooter>
                <Link to={`/types/${eventType.id}`} className={buttonVariants()}>
                  Выбрать
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
