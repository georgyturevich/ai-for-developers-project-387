import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, Navigate, useNavigate, useParams, useSearchParams } from "react-router";
import { api } from "@/api/client";
import { API_ERROR_CODES, unwrap } from "@/api/errors";
import { useEventTypes } from "@/api/queries";
import { PageError } from "@/components/page-error";
import { Button, buttonVariants } from "@/components/ui/button";
import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { NotFoundPage } from "@/pages/not-found-page";
import { OWNER_TIMEZONE_LABEL, formatDayAndTimeRange } from "@/lib/datetime";
import { handleFormContractError } from "@/lib/form-errors";
import { type BookingFormValues, bookingFormSchema } from "@/lib/schemas";

export function BookingFormPage() {
  const { eventTypeId } = useParams<{ eventTypeId: string }>();
  const [searchParams] = useSearchParams();
  const start = searchParams.get("start");
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const eventTypesQuery = useEventTypes();
  const [notFound, setNotFound] = useState(false);

  const form = useForm<BookingFormValues>({
    resolver: zodResolver(bookingFormSchema),
    defaultValues: { name: "", email: "", comment: "" },
  });

  const mutation = useMutation({
    mutationFn: (values: BookingFormValues) =>
      unwrap(
        api.POST("/bookings", {
          body: { eventTypeId: eventTypeId ?? "", start: start ?? "", guest: values },
        }),
      ),
    onSuccess: (booking) => {
      navigate("/confirmation", { state: { booking } });
    },
    onError: (error) => {
      handleFormContractError(
        error,
        form,
        {
          // Слот заняли, пока гость заполнял форму: остаёмся на форме (введённые
          // данные не теряем), список слотов инвалидируем — обновится при возврате.
          [API_ERROR_CODES.slotUnavailable]: () => {
            void queryClient.invalidateQueries({ queryKey: ["slots", eventTypeId] });
            form.setError("root", {
              message: "Этот слот только что заняли. Вернитесь и выберите другое время.",
            });
          },
          [API_ERROR_CODES.eventTypeNotFound]: () => setNotFound(true),
        },
        "Не удалось записаться. Попробуйте ещё раз.",
      );
    },
  });

  if (!eventTypeId || !start) {
    return <Navigate to="/" replace />;
  }

  if (notFound) {
    return <NotFoundPage title="Тип события не найден" />;
  }

  if (eventTypesQuery.isPending) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const eventType = eventTypesQuery.data.find((item) => item.id === eventTypeId);
  if (!eventType) {
    if (eventTypesQuery.isError) {
      return <PageError onRetry={() => eventTypesQuery.refetch()} />;
    }
    return <NotFoundPage title="Тип события не найден" />;
  }

  const errors = form.formState.errors;

  return (
    <div className="flex max-w-lg flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold">Запись: {eventType.name}</h1>
        <p className="text-muted-foreground">
          {formatDayAndTimeRange(start, eventType.durationInMinutes)} ({OWNER_TIMEZONE_LABEL})
        </p>
      </div>

      <form
        className="flex flex-col gap-5"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <Field>
          <FieldLabel htmlFor="guest-name">Имя</FieldLabel>
          <Input id="guest-name" autoComplete="name" {...form.register("name")} />
          <FieldError>{errors.name?.message}</FieldError>
        </Field>

        <Field>
          <FieldLabel htmlFor="guest-email">Email</FieldLabel>
          <Input id="guest-email" type="email" autoComplete="email" {...form.register("email")} />
          <FieldError>{errors.email?.message}</FieldError>
        </Field>

        <Field>
          <FieldLabel htmlFor="guest-comment">Комментарий</FieldLabel>
          <Textarea id="guest-comment" rows={3} {...form.register("comment")} />
          <FieldDescription>Необязательно</FieldDescription>
          <FieldError>{errors.comment?.message}</FieldError>
        </Field>

        {errors.root ? <FieldError>{errors.root.message}</FieldError> : null}

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" size="lg" disabled={mutation.isPending}>
            {mutation.isPending ? "Записываем…" : "Записаться"}
          </Button>
          <Link
            to={`/types/${eventType.id}`}
            className={buttonVariants({ variant: "outline", size: "lg" })}
          >
            Выбрать другое время
          </Link>
        </div>
      </form>
    </div>
  );
}
