import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import { unwrap } from "./errors";

export function useEventTypes() {
  return useQuery({
    queryKey: ["event-types"],
    queryFn: () => unwrap(api.GET("/event-types")),
  });
}

export function useSlots(eventTypeId: string) {
  return useQuery({
    queryKey: ["slots", eventTypeId],
    queryFn: () =>
      unwrap(
        api.GET("/event-types/{eventTypeId}/slots", {
          params: { path: { eventTypeId } },
        }),
      ),
  });
}

export function useUpcomingBookings() {
  return useQuery({
    queryKey: ["bookings"],
    queryFn: () => unwrap(api.GET("/bookings")),
  });
}
