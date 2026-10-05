import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useEffect, useState, type FormEvent, type ReactNode } from "react";
import { api, ApiError, setCsrfToken, pagesDeployment, fullAppUrl, isHealth } from "../../shared/api/client";
import { EventStreamBridge } from "../../shared/api/eventStream";
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
    if (pagesDeployment && import.meta.env.VITE_FULL_APP_ONLY === 'true' && fullAppUrl) {
      await api('/health/ready', undefined, isHealth);
      window.location.replace(`${fullAppUrl.replace(/\/$/, '')}/demo`);
      await new Promise<never>(() => {});
    }
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
      setCsrfToken(value.csrf_token);
      if (pagesDeployment) {
        try { await api<SessionInfo>('/access/session'); }
        catch { throw new Error('This browser could not retain the cross-site session. Open the complete demo below to sign in.'); }
      }
      setPassword(""); setExpired(false);
      queryClient.clear(); queryClient.setQueryData(["session"], value);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Sign in failed"); }
    finally { setBusy(false); }
  }
  if (session.data && !expired) return <SessionContext.Provider value={session.data}><EventStreamBridge/>{children}</SessionContext.Provider>;
  if (session.isPending && !expired) return <div className="async-state loading-state" role="status"><span className="spinner"/><strong>Opening your workspace…</strong></div>;
  const signInRequired = expired || session.error instanceof ApiError && session.error.status === 401;
  if (!signInRequired) return <main className="login-shell"><section className="login-card" role="alert"><span className="brand-mark"><Icon name="aircraft" size={28}/></span><h1>Demo backend offline</h1><p>Aircraft maintenance connects AI engine-health evidence with parts, crew, a checked schedule and human approval.</p><p>The demo server is currently unreachable. Its host needs to keep Docker and the HTTPS tunnel running. No calculations are available while disconnected.</p><button onClick={() => void session.refetch()}>Try again</button>{fullAppUrl && <p><a className="button-secondary" href={`${fullAppUrl.replace(/\/$/, '')}/demo`}>Open complete demo</a></p>}</section></main>;
  return <main className="login-shell"><section className="login-card"><span className="brand-mark"><Icon name="aircraft" size={28}/></span><h1>Sign in to Aircraft maintenance</h1><p>Use your assigned maintenance workspace account.</p>{pagesDeployment && fullAppUrl && <p><a className="button-secondary" href={`${fullAppUrl.replace(/\/$/, '')}/demo`}>Open complete demo</a><small>Use this when your browser blocks cross-site sign-in.</small></p>}<form onSubmit={(event) => void login(event)}><label>Account ID<input autoComplete="username" value={user} onChange={(event) => setUser(event.target.value)} required maxLength={64}/></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required maxLength={256}/></label>{error && <p role="alert" className="form-error">{error}</p>}<button className="button" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button></form>{pagesDeployment && fullAppUrl && <a className="button-secondary" href={`${fullAppUrl.replace(/\/$/, '')}/demo`}>Open the complete demo</a>}<small>Evidence supports human review.</small></section></main>;
}
