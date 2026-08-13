import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import type { z } from "zod";
import { api } from "@/api/client";
import { API_ERROR_CODES, unwrap } from "@/api/errors";
import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { handleFormContractError } from "@/lib/form-errors";
import { type EventTypeFormValues, eventTypeFormSchema } from "@/lib/schemas";

type EventTypeFormInput = z.input<typeof eventTypeFormSchema>;

export function EventTypeNewPage() {
  const navigate = useNavigate();

  const form = useForm<EventTypeFormInput, undefined, EventTypeFormValues>({
    resolver: zodResolver(eventTypeFormSchema),
    defaultValues: { id: "", name: "", description: "" },
  });

  const mutation = useMutation({
    mutationFn: (values: EventTypeFormValues) =>
      unwrap(api.POST("/event-types", { body: values })),
    onSuccess: () => {
      toast.success("Тип события создан");
      navigate("/");
    },
    onError: (error) => {
      handleFormContractError(
        error,
        form,
        {
          [API_ERROR_CODES.duplicateSlug]: () =>
            form.setError("id", { message: "Этот адрес уже занят" }),
        },
        "Не удалось создать тип события. Попробуйте ещё раз.",
      );
    },
  });

  const errors = form.formState.errors;

  return (
    <div className="flex max-w-lg flex-col gap-6">
      <h1 className="text-2xl font-semibold">Новый тип события</h1>

      <form
        className="flex flex-col gap-5"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <Field>
          <FieldLabel htmlFor="event-type-id">Адрес (slug)</FieldLabel>
          <Input id="event-type-id" placeholder="strizhka" {...form.register("id")} />
          <FieldDescription>
            Строчные латинские буквы, цифры и дефисы. Адрес появится в ссылке для записи. Изменить
            или удалить тип события потом нельзя.
          </FieldDescription>
          <FieldError>{errors.id?.message}</FieldError>
        </Field>

        <Field>
          <FieldLabel htmlFor="event-type-name">Название</FieldLabel>
          <Input id="event-type-name" placeholder="Стрижка" {...form.register("name")} />
          <FieldError>{errors.name?.message}</FieldError>
        </Field>

        <Field>
          <FieldLabel htmlFor="event-type-description">Описание</FieldLabel>
          <Textarea
            id="event-type-description"
            rows={3}
            placeholder="Что ждёт гостя на встрече"
            {...form.register("description")}
          />
          <FieldDescription>Видно гостям в каталоге. Можно оставить пустым.</FieldDescription>
          <FieldError>{errors.description?.message}</FieldError>
        </Field>

        <Field>
          <FieldLabel htmlFor="event-type-duration">Длительность, минут</FieldLabel>
          <Input
            id="event-type-duration"
            type="number"
            min={1}
            max={540}
            step={1}
            {...form.register("durationInMinutes")}
          />
          <FieldDescription>
            От 1 до 540: слот должен целиком помещаться в рабочие часы 09:00–18:00.
          </FieldDescription>
          <FieldError>{errors.durationInMinutes?.message}</FieldError>
        </Field>

        {errors.root ? <FieldError>{errors.root.message}</FieldError> : null}

        <div>
          <Button type="submit" size="lg" disabled={mutation.isPending}>
            {mutation.isPending ? "Создаём…" : "Создать тип события"}
          </Button>
        </div>
      </form>
    </div>
  );
}
