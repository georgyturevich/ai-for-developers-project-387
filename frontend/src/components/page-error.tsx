import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

// Сетевая/серверная ошибка загрузки: inline-состояние страницы + toast с retry.
export function PageError({ onRetry }: { onRetry: () => void }) {
  const retryRef = useRef(onRetry);
  retryRef.current = onRetry;

  useEffect(() => {
    toast.error("Не удалось загрузить данные. Проверьте соединение.", {
      action: { label: "Повторить", onClick: () => retryRef.current() },
    });
  }, []);

  return (
    <div className="flex flex-col items-center gap-4 py-16 text-center">
      <p className="text-muted-foreground">
        Не удалось загрузить данные. Проверьте соединение и попробуйте ещё раз.
      </p>
      <Button variant="outline" onClick={onRetry}>
        Повторить
      </Button>
    </div>
  );
}
