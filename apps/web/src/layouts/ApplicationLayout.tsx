import { useSession } from "../features/access/SessionGate";
import * as Dialog from "@radix-ui/react-dialog";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { api, arrayOf, isAlert, isHealth, type Alert } from "../shared/api/client";
import { Icon, type IconName } from "../shared/ui/Icon";
const links: { to: string; label: string; icon: IconName }[] = [
  { to:"/overview",label:"Start",icon:"grid" },{ to:"/fleet",label:"Aircraft",icon:"aircraft" },{ to:"/demo",label:"Try demo",icon:"activity" },{ to:"/planning",label:"Planning",icon:"calendar" },
];
const tools: { to: string; label: string; icon: IconName }[] = [
  { to:"/fleet/register",label:"Fleet register",icon:"grid" },{ to:"/alerts",label:"Alerts",icon:"bell" },{ to:"/inventory",label:"Parts & deliveries",icon:"box" },{ to:"/scenarios",label:"What-if comparisons",icon:"chart" },{ to:"/ai",label:"AI & evidence",icon:"activity" },
];
export function ApplicationLayout() {
  const location=useLocation(),session=useSession();
  const [mobileOpen,setMobileOpen]=useState(false);
  const health=useQuery({queryKey:["api-health"],queryFn:()=>api("/health/ready",undefined,isHealth),refetchInterval:30_000,retry:false});
  const alerts=useQuery({queryKey:["alerts"],queryFn:()=>api<Alert[]>("/alerts",undefined,arrayOf(isAlert))});
  const pending=alerts.data?.filter(alert=>!alert.acknowledgements.length).length;
  const destinations=(items:typeof links)=>items.map(link=><NavLink key={link.to} to={link.to} className={({isActive})=>isActive||(link.to==='/fleet'&&(location.pathname==='/fleet/register'||location.pathname.startsWith('/components/')))?'active':undefined} onClick={()=>setMobileOpen(false)}><Icon name={link.icon} size={18}/><span>{link.label}</span>{link.to==='/alerts'&&pending!==undefined&&pending>0&&<span className="nav-count">{pending}</span>}</NavLink>);
  const navigation=<nav aria-label="Primary navigation">{destinations(links)}</nav>;
  const supporting=<nav aria-label="Supporting tools">{destinations(tools)}</nav>;
  return <Dialog.Root open={mobileOpen} onOpenChange={setMobileOpen}><div className="inspection-shell"><a className="skip-link" href="#main-content">Skip to content</a><header className="product-header"><NavLink className="product-brand" to="/overview"><Icon name="aircraft" size={22}/><span>Aircraft maintenance<small>PS 26249</small></span></NavLink><div className="desktop-navigation">{navigation}</div><div className="product-account"><span className={`connection-status ${health.isError?'offline':''}`}><i/>{health.isPending?'Connecting…':health.isError?'Demo backend offline':'API connected'}</span><span className="environment-tag">{session?.authentication==='server session'?'SIGNED IN':'LOCAL DEMO'}</span><details className="account-menu"><summary aria-label="Account details"><Icon name="user" size={18}/></summary><div><strong>{session?.id??'Workspace user'}</strong><p>{session?.role??'Authenticated access'}</p>{session?.authentication==='server session'&&<button onClick={()=>void api('/access/session',{method:'DELETE'}).then(()=>window.dispatchEvent(new Event('fleet:session-expired')))}>Sign out</button>}</div></details><Dialog.Trigger asChild><button className="button-secondary workspace-navigation-toggle" aria-label="Open navigation"><span className="toggle-copy">More tools</span><Icon name="menu" size={18}/></button></Dialog.Trigger></div></header><Dialog.Portal><Dialog.Overlay className="nav-overlay"/><Dialog.Content className="mobile-destinations" aria-describedby={undefined}><Dialog.Title>Workspace navigation</Dialog.Title>{navigation}<p className="eyebrow">SUPPORTING TOOLS</p>{supporting}<Dialog.Close asChild><button className="button-secondary">Close navigation</button></Dialog.Close></Dialog.Content></Dialog.Portal><main id="main-content" className="page" tabIndex={-1} key={location.pathname}><Outlet/></main><footer className="workspace-footer"><span>Aircraft maintenance · Synthetic demonstrator workspace</span><span>Evidence supports human review. No aircraft clearance.</span></footer></div></Dialog.Root>;
}
