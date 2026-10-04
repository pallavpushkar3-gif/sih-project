import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

const eventTypes = [
  "resync",
  "job.queued",
  "job.running",
  "job.requeued",
  "job.cancellation_requested",
  "job.cancelled",
  "job.failed",
  "job.succeeded",
] as const;

export function EventStreamBridge() {
  const client = useQueryClient();

  useEffect(() => {
    const source = new EventSource("/api/events");
    const refresh = () => {
      void client.invalidateQueries({ queryKey: ["jobs"] });
      void client.invalidateQueries({ queryKey: ["plans"] });
      void client.invalidateQueries({ queryKey: ["scenario-runs"] });
      void client.invalidateQueries({ queryKey: ["inventory"] });
      void client.invalidateQueries({ queryKey: ["arrivals"] });
      void client.invalidateQueries({ queryKey: ["alerts"] });
    };
    const expired = () => { source.close(); window.dispatchEvent(new Event("fleet:session-expired")); };
    source.addEventListener("auth.required", expired);
    for (const type of eventTypes) source.addEventListener(type, refresh);
    return () => {
      for (const type of eventTypes) source.removeEventListener(type, refresh);
      source.removeEventListener("auth.required", expired);
      source.close();
    };
  }, [client]);

  return null;
}
