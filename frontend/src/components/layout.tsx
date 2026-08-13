import { Link, Outlet } from "react-router";
import { Toaster } from "@/components/ui/sonner";
import { OWNER_TIMEZONE_LABEL } from "@/lib/datetime";

export function Layout() {
  return (
    <div className="flex min-h-svh flex-col">
      <header className="border-b">
        <div className="mx-auto flex w-full max-w-3xl items-baseline gap-3 px-4 py-4">
          <Link to="/" className="text-lg font-semibold">
            Calendar Bookings
          </Link>
          <span className="text-sm text-muted-foreground">
            всё время — московское ({OWNER_TIMEZONE_LABEL})
          </span>
        </div>
      </header>
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6">
        <Outlet />
      </main>
      <footer className="border-t">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between px-4 py-4 text-sm">
          <Link to="/owner" className="text-muted-foreground hover:text-foreground hover:underline">
            Владельцу
          </Link>
          <span className="text-muted-foreground">&copy; Cal Bookings Lab</span>
        </div>
      </footer>
      <Toaster richColors position="top-center" />
    </div>
  );
}
