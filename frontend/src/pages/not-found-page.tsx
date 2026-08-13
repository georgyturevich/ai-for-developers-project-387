import { Link } from "react-router";
import { buttonVariants } from "@/components/ui/button";

export function NotFoundPage({ title = "Страница не найдена" }: { title?: string }) {
  return (
    <div className="flex flex-col items-center gap-4 py-16 text-center">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <Link to="/" className={buttonVariants({ variant: "outline" })}>
        К списку типов событий
      </Link>
    </div>
  );
}
