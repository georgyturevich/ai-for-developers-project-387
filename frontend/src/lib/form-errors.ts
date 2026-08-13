import { toast } from "sonner";
import { API_ERROR_CODES, ContractError } from "@/api/errors";

interface FormLike {
  setError: (name: "root", error: { message: string }) => void;
}

// Единый разбор ошибок API в формах: специфичные коды — в handlers,
// validation_failed — в корневую ошибку формы с сообщением сервера,
// всё остальное (сеть, 5xx) — toast.
export function handleFormContractError(
  error: unknown,
  form: FormLike,
  handlers: Partial<Record<string, () => void>>,
  fallbackMessage: string,
): void {
  if (error instanceof ContractError) {
    const handler = error.code === undefined ? undefined : handlers[error.code];
    if (handler) {
      handler();
      return;
    }
    if (error.code === API_ERROR_CODES.validationFailed) {
      form.setError("root", { message: error.message });
      return;
    }
  }
  toast.error(fallbackMessage);
}
