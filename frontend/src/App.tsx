import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router";
import { Layout } from "@/components/layout";
import { BookingFormPage } from "@/pages/booking-form-page";
import { CatalogPage } from "@/pages/catalog-page";
import { ConfirmationPage } from "@/pages/confirmation-page";
import { EventTypeNewPage } from "@/pages/event-type-new-page";
import { NotFoundPage } from "@/pages/not-found-page";
import { OwnerBookingsPage } from "@/pages/owner-bookings-page";
import { SlotsPage } from "@/pages/slots-page";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<CatalogPage />} />
            <Route path="types/:eventTypeId" element={<SlotsPage />} />
            <Route path="types/:eventTypeId/book" element={<BookingFormPage />} />
            <Route path="confirmation" element={<ConfirmationPage />} />
            <Route path="owner" element={<OwnerBookingsPage />} />
            <Route path="owner/event-types/new" element={<EventTypeNewPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
