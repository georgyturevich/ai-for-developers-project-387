import type { ApiErrorBody } from "./types";

// Коды заявлены в описании ApiError.code в контракте (main.tsp), а не формальным enum.
export const API_ERROR_CODES = {
  validationFailed: "validation_failed",
  eventTypeNotFound: "event_type_not_found",
  duplicateSlug: "duplicate_slug",
  slotUnavailable: "slot_unavailable",
} as const;

export class ContractError extends Error {
  readonly status: number;
  readonly body: ApiErrorBody | undefined;

  constructor(status: number, body?: ApiErrorBody) {
    super(body?.message ?? `Запрос завершился с ошибкой ${status}`);
    this.name = "ContractError";
    this.status = status;
    this.body = body;
  }

  get code(): string | undefined {
    return this.body?.code;
  }
}

interface FetchResult<T> {
  data?: T;
  error?: unknown;
  response: Response;
}

// openapi-fetch не бросает исключений на HTTP-ошибки — переводим их в ContractError,
// чтобы TanStack Query видел состояние ошибки.
export async function unwrap<T>(result: Promise<FetchResult<T>>): Promise<T> {
  const { data, error, response } = await result;
  if (error !== undefined && error !== null) {
    throw new ContractError(response.status, error as ApiErrorBody);
  }
  if (data === undefined) {
    throw new ContractError(response.status);
  }
  return data;
}
