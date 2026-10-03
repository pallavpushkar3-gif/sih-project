import type {PropsWithChildren} from "react";

type AsyncStateProps = {
  loading: boolean;
  error: Error | null;
  empty?: boolean;
  emptyMessage?: string;
} & PropsWithChildren;

export function AsyncState({ loading, error, empty, emptyMessage, children }: AsyncStateProps) {
  if (loading) return <div className="state" role="status">Loading authoritative records…</div>;
  if (error) return <div className="state error" role="alert">Unable to load: {error.message}</div>;
  if (empty) return <div className="state">{emptyMessage ?? "No records are available for this view."}</div>;
  return <>{children}</>;
}
