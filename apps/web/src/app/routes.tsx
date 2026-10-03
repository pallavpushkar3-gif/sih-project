import {createBrowserRouter,Navigate} from "react-router-dom";
import {ApplicationLayout} from "../layouts/ApplicationLayout";
import {FleetPage} from "../features/fleet/FleetPage";
import {ComponentPage} from "../features/components/ComponentPage";
import {AlertsPage} from "../features/alerts/AlertsPage";
import {PlanningPage} from "../features/planning/PlanningPage";
import {InventoryPage} from "../features/inventory/InventoryPage";
import {ScenariosPage} from "../features/scenarios/ScenariosPage";
export const router=createBrowserRouter([{path:"/",element:<ApplicationLayout/>,children:[{index:true,element:<Navigate to="/fleet" replace/>},{path:"fleet",element:<FleetPage/>},{path:"components/:componentId",element:<ComponentPage/>},{path:"alerts",element:<AlertsPage/>},{path:"planning",element:<PlanningPage/>},{path:"inventory",element:<InventoryPage/>},{path:"scenarios",element:<ScenariosPage/>}]}]);
