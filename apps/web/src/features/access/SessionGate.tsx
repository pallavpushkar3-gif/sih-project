import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useEffect, useState, type FormEvent, type ReactNode } from "react";
import { api, ApiError, setCsrfToken } from "../../shared/api/client";
import { Icon } from "../../shared/ui/Icon";

type SessionInfo = { id: string; role: string; authentication: string; csrf_token: string | null };
const SessionContext = createContext<SessionInfo | null>(null);
export function useSession() { return useContext(SessionContext); }
export function SessionGate({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [expired, setExpired] = useState(false);
  useEffect(() => {
    function endSession() { setExpired(true); setCsrfToken(null); queryClient.clear(); }
    window.addEventListener("fleet:session-expired", endSession);
    return () => window.removeEventListener("fleet:session-expired", endSession);
  }, [queryClient]);
  const session = useQuery({ queryKey: ["session"], enabled: !expired, retry: false, queryFn: async () => {
    const value = await api<SessionInfo>("/access/session");
    setCsrfToken(value.csrf_token);
    return value;
  }});
  const [user, setUser] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function login(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const value = await api<SessionInfo>("/access/session", { method: "POST", body: JSON.stringify({ user_id: user, password }) });
      setPassword(""); setCsrfToken(value.csrf_token); setExpired(false);
      queryClient.clear(); queryClient.setQueryData(["session"], value);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Sign in failed"); }
    finally { setBusy(false); }
  }
  if (session.data && !expired) return <SessionContext.Provider value={session.data}>{children}</SessionContext.Provider>;
  if (session.isPending && !expired) return <div className="async-state loading-state" role="status"><span className="spinner"/><strong>Opening your workspace…</strong></div>;
  const signInRequired = expired || session.error instanceof ApiError && session.error.status === 401;
  if (!signInRequired) return <div className="async-state error-state" role="alert"><h1>Workspace unavailable</h1><p>{session.error?.message}</p><button onClick={() => void session.refetch()}>Try again</button></div>;
  return <main className="login-shell"><section className="login-card"><span className="brand-mark"><Icon name="aircraft" size={28}/></span><h1>Sign in to Aircraft maintenance</h1><p>Use your assigned maintenance workspace account.</p><form onSubmit={(event) => void login(event)}><label>Account ID<input autoComplete="username" value={user} onChange={(event) => setUser(event.target.value)} required maxLength={64}/></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required maxLength={256}/></label>{error && <p role="alert" className="form-error">{error}</p>}<button className="button" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button></form><small>Evidence supports human review.</small></section></main>;
}
