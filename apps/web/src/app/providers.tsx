import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { PropsWithChildren } from "react";
import { EventStreamBridge } from "../shared/api/eventStream";
const client=new QueryClient({defaultOptions:{queries:{staleTime:15_000,retry:1}}});
export function AppProviders({children}:PropsWithChildren){return <QueryClientProvider client={client}><EventStreamBridge />{children}</QueryClientProvider>}
