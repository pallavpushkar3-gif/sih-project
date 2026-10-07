import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

type AsOfValue = { asOf: string | null; setAsOf: (value: string | null) => void };
const AsOfContext = createContext<AsOfValue>({ asOf: null, setAsOf: () => {} });
const storageKey = "ops:replay-as-of";

function readStored(): string | null {
  try { return window.sessionStorage.getItem(storageKey); } catch { return null; }
}

/** Replay date shared by every fleet-health screen. ``null`` means the latest engine state. */
export function AsOfProvider({ children }: { children: ReactNode }) {
  const [asOf, setState] = useState<string | null>(readStored);
  const setAsOf = useCallback((value: string | null) => {
    setState(value);
    try {
      if (value) window.sessionStorage.setItem(storageKey, value);
      else window.sessionStorage.removeItem(storageKey);
    } catch { /* storage unavailable: replay still works for this page view */ }
  }, []);
  const value = useMemo(() => ({ asOf, setAsOf }), [asOf, setAsOf]);
  return <AsOfContext.Provider value={value}>{children}</AsOfContext.Provider>;
}

export function useAsOf() { return useContext(AsOfContext); }

export function addDays(iso: string, days: number) {
  const date = new Date(`${iso}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}
export function dayDiff(from: string, to: string) {
  return Math.round((Date.parse(`${to}T00:00:00Z`) - Date.parse(`${from}T00:00:00Z`)) / 86_400_000);
}
