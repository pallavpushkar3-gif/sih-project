import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

const eventTypes = [
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
    };
    for (const type of eventTypes) source.addEventListener(type, refresh);
    return () => {
      for (const type of eventTypes) source.removeEventListener(type, refresh);
      source.close();
    };
  }, [client]);

  return null;
}
