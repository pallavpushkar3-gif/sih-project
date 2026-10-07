import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, createHashRouter, Link, Navigate, useRouteError } from "react-router-dom";
import { SessionGate } from "../features/access/SessionGate";
import { AsOfProvider } from "../features/ops/AsOf";
import { OpsLayout } from "../features/ops/OpsLayout";
import { RoleProvider } from "../features/ops/roles";
import { ToastProvider } from "../features/ops/ui";
const InspectionPage = lazy(() => import("../features/inspection/InspectionPage").then((module) => ({ default: module.InspectionPage })));
const OverviewPage = lazy(() => import("../features/fleet/OverviewPage").then((module) => ({ default: module.OverviewPage })));
const CustomerTrialPage = lazy(() => import("../features/demo/CustomerTrialPage").then(module => ({ default: module.CustomerTrialPage })));
const AIPage = lazy(() => import("../features/health/AIPage").then((module) => ({ default: module.AIPage })));
const FleetPage = lazy(() => import("../features/fleet/FleetPage").then((module) => ({ default: module.FleetPage })));
const ComponentPage = lazy(() => import("../features/components/ComponentPage").then((module) => ({ default: module.ComponentPage })));
const AlertsPage = lazy(() => import("../features/alerts/AlertsPage").then((module) => ({ default: module.AlertsPage })));
const PlanningPage = lazy(() => import("../features/planning/PlanningPage").then((module) => ({ default: module.PlanningPage })));
const InventoryPage = lazy(() => import("../features/inventory/InventoryPage").then((module) => ({ default: module.InventoryPage })));
const ScenariosPage = lazy(() => import("../features/scenarios/ScenariosPage").then((module) => ({ default: module.ScenariosPage })));
const workflow = () => import("../features/ops/WorkflowPages");
const FleetDashboard = lazy(() => import("../features/ops/FleetDashboard").then((module) => ({ default: module.FleetDashboard })));
const FocusRedirect = lazy(() => import("../features/ops/Focus").then((module) => ({ default: module.FocusRedirect })));
const HomeRedirect = lazy(() => workflow().then((module) => ({ default: module.HomeRedirect })));
const WelcomePage = lazy(() => workflow().then((module) => ({ default: module.WelcomePage })));
const ReviewPage = lazy(() => workflow().then((module) => ({ default: module.ReviewPage })));
const PlanPage = lazy(() => workflow().then((module) => ({ default: module.PlanPage })));
const PartsPage = lazy(() => workflow().then((module) => ({ default: module.PartsPage })));
const StatusPage = lazy(() => workflow().then((module) => ({ default: module.StatusPage })));
const AircraftListPage = lazy(() => import("../features/ops/AircraftPages").then((module) => ({ default: module.AircraftListPage })));
const AircraftDetailPage = lazy(() => import("../features/ops/AircraftPages").then((module) => ({ default: module.AircraftDetailPage })));
const ComponentHealthPage = lazy(() => import("../features/ops/ComponentHealthPage").then((module) => ({ default: module.ComponentHealthPage })));
const AdvisoriesPage = lazy(() => import("../features/ops/AdvisoriesPage").then((module) => ({ default: module.AdvisoriesPage })));
const MaintenancePage = lazy(() => import("../features/ops/MaintenancePage").then((module) => ({ default: module.MaintenancePage })));
const SparesPage = lazy(() => import("../features/ops/SparesPage").then((module) => ({ default: module.SparesPage })));
const SimulatorPage = lazy(() => import("../features/ops/SimulatorPage").then((module) => ({ default: module.SimulatorPage })));
const AnalyticsPage = lazy(() => import("../features/ops/AnalyticsPage").then((module) => ({ default: module.AnalyticsPage })));
const DataPage = lazy(() => import("../features/ops/DataPage").then((module) => ({ default: module.DataPage })));
const NotificationsPage = lazy(() => import("../features/ops/DataPage").then((module) => ({ default: module.NotificationsPage })));
function RouteFailure() {
  const error = useRouteError();
  const missing = typeof error === "object" && error !== null && "status" in error && error.status === 404;
  return <div className="page"><div className="async-state empty-state"><h1>{missing ? "Page not found" : "This view couldn’t open"}</h1><p>{missing ? "The page address is not part of this workspace." : "Please reload the page. Your saved records remain on the server."}</p><Link className="button" to="/dashboard">Return to dashboard</Link></div></div>;
}
const loading = <div className="async-state loading-state" role="status"><span className="spinner"/><strong>Opening workspace…</strong></div>;
const createRouter = import.meta.env.VITE_PAGES === 'true' ? createHashRouter : createBrowserRouter;
const page = (element: ReactNode) => <Suspense fallback={loading}>{element}</Suspense>;
export const router = createRouter([{ path:"/", element:<SessionGate><RoleProvider><AsOfProvider><ToastProvider><OpsLayout/></ToastProvider></AsOfProvider></RoleProvider></SessionGate>, errorElement:<RouteFailure/>, children:[
  { index:true, element:import.meta.env.VITE_PAGES === 'true' ? <Navigate to="/demo" replace/> : page(<HomeRedirect/>) },
  { path:"home", element:page(<HomeRedirect/>) },
  { path:"welcome", element:page(<WelcomePage/>) },
  { path:"review", element:page(<ReviewPage/>) },
  { path:"plan", element:page(<PlanPage/>) },
  { path:"parts", element:page(<PartsPage/>) },
  { path:"status", element:page(<StatusPage/>) },
  { path:"dashboard", element:page(<FleetDashboard/>) },
  { path:"aircraft-detail", element:page(<FocusRedirect kind="aircraft"/>) },
  { path:"component-health", element:page(<FocusRedirect kind="component"/>) },
  { path:"aircraft", element:page(<AircraftListPage/>) },
  { path:"aircraft/:aircraftId", element:page(<AircraftDetailPage/>) },
  { path:"health/:componentId", element:page(<ComponentHealthPage/>) },
  { path:"advisories", element:page(<AdvisoriesPage/>) },
  { path:"maintenance", element:page(<MaintenancePage/>) },
  { path:"spares", element:page(<SparesPage/>) },
  { path:"simulator", element:page(<SimulatorPage/>) },
  { path:"analytics", element:page(<AnalyticsPage/>) },
  { path:"data", element:page(<DataPage/>) },
  { path:"notifications", element:page(<NotificationsPage/>) },
  { path:"overview", element:<Suspense fallback={loading}><OverviewPage/></Suspense> },
  { path:"fleet", element:<Suspense fallback={loading}><InspectionPage/></Suspense> },
  { path:"demo", element:<Suspense fallback={loading}><CustomerTrialPage/></Suspense> },
  { path:"ai", element:<Suspense fallback={loading}><AIPage/></Suspense> },
  { path:"fleet/register", element:<Suspense fallback={loading}><FleetPage/></Suspense> },
  { path:"components/:componentId", element:<Suspense fallback={loading}><ComponentPage/></Suspense> },
  { path:"alerts", element:<Suspense fallback={loading}><AlertsPage/></Suspense> },
  { path:"planning", element:<Suspense fallback={loading}><PlanningPage/></Suspense> },
  { path:"inventory", element:<Suspense fallback={loading}><InventoryPage/></Suspense> },
  { path:"scenarios", element:<Suspense fallback={loading}><ScenariosPage/></Suspense> },
  { path:"*", element:<RouteFailure/> },
] }]);
