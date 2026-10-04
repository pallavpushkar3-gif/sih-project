import type { PropsWithChildren } from "react";
import { Icon } from "./Icon";
type AsyncStateProps = PropsWithChildren<{ loading: boolean; error: Error | null; empty?: boolean; emptyMessage?: string; onRetry?: () => void }>;
export function AsyncState({ loading, error, empty, emptyMessage, onRetry, children }: AsyncStateProps) {
  if (loading) return <div className="async-state loading-state" role="status"><span className="spinner"/><div><strong>Loading workspace records</strong><p>Retrieving the latest saved data.</p></div></div>;
  if (error) return <div className="async-state error-state" role="alert"><Icon name="warning" size={24}/><div><strong>We couldn’t load these records</strong><p>{error.message}</p>{onRetry && <button className="secondary" onClick={onRetry}><Icon name="refresh" size={16}/>Try again</button>}</div></div>;
  if (empty) return <div className="async-state empty-state"><span className="empty-icon"><Icon name="file" size={25}/></span><strong>{emptyMessage ?? "No records yet"}</strong><p>New records will appear here when they are available.</p></div>;
  return <>{children}</>;
}
