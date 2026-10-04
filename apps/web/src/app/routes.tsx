import { lazy, Suspense } from "react";
import { createBrowserRouter, Link, Navigate, useRouteError } from "react-router-dom";
import { SessionGate } from "../features/access/SessionGate";
import { ApplicationLayout } from "../layouts/ApplicationLayout";
const InspectionPage = lazy(() => import("../features/inspection/InspectionPage").then((module) => ({ default: module.InspectionPage })));
const FleetPage = lazy(() => import("../features/fleet/FleetPage").then((module) => ({ default: module.FleetPage })));
const ComponentPage = lazy(() => import("../features/components/ComponentPage").then((module) => ({ default: module.ComponentPage })));
const AlertsPage = lazy(() => import("../features/alerts/AlertsPage").then((module) => ({ default: module.AlertsPage })));
const PlanningPage = lazy(() => import("../features/planning/PlanningPage").then((module) => ({ default: module.PlanningPage })));
const InventoryPage = lazy(() => import("../features/inventory/InventoryPage").then((module) => ({ default: module.InventoryPage })));
const ScenariosPage = lazy(() => import("../features/scenarios/ScenariosPage").then((module) => ({ default: module.ScenariosPage })));
function RouteFailure() {
  const error = useRouteError();
  const missing = typeof error === "object" && error !== null && "status" in error && error.status === 404;
  return <div className="page"><div className="async-state empty-state"><h1>{missing ? "Page not found" : "This view couldn’t open"}</h1><p>{missing ? "The page address is not part of this workspace." : "Please reload the page. Your saved records remain on the server."}</p><Link className="button" to="/fleet">Return to fleet</Link></div></div>;
}
const loading = <div className="async-state loading-state" role="status"><span className="spinner"/><strong>Opening workspace…</strong></div>;
export const router = createBrowserRouter([{ path:"/", element:<SessionGate><ApplicationLayout/></SessionGate>, errorElement:<RouteFailure/>, children:[
  { index:true, element:<Navigate to="/fleet" replace/> },
  { path:"fleet", element:<Suspense fallback={loading}><InspectionPage/></Suspense> },
  { path:"fleet/register", element:<Suspense fallback={loading}><FleetPage/></Suspense> },
  { path:"components/:componentId", element:<Suspense fallback={loading}><ComponentPage/></Suspense> },
  { path:"alerts", element:<Suspense fallback={loading}><AlertsPage/></Suspense> },
  { path:"planning", element:<Suspense fallback={loading}><PlanningPage/></Suspense> },
  { path:"inventory", element:<Suspense fallback={loading}><InventoryPage/></Suspense> },
  { path:"scenarios", element:<Suspense fallback={loading}><ScenariosPage/></Suspense> },
  { path:"*", element:<RouteFailure/> },
] }]);
