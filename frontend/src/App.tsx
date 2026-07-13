import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppShell } from "@/components/layout/AppShell";
import { Skeleton } from "@/components/ui/skeleton";

// Route-level code splitting — each page (and the chart/animation libraries
// only some of them use) loads on demand instead of one ~900KB entry chunk.
const Overview = lazy(() => import("@/pages/Overview").then((m) => ({ default: m.Overview })));
const Analytics = lazy(() => import("@/pages/Analytics").then((m) => ({ default: m.Analytics })));
const DataExplorer = lazy(() => import("@/pages/DataExplorer").then((m) => ({ default: m.DataExplorer })));
const QueryExplorer = lazy(() => import("@/pages/QueryExplorer").then((m) => ({ default: m.QueryExplorer })));
const Insights = lazy(() => import("@/pages/Insights").then((m) => ({ default: m.Insights })));
const About = lazy(() => import("@/pages/About").then((m) => ({ default: m.About })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

function PageFallback() {
  return (
    <div className="flex flex-col gap-4">
      <Skeleton className="h-10 w-64" />
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-64" />
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider delayDuration={150}>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route element={<AppShell />}>
              <Route index element={<Overview />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="explorer" element={<DataExplorer />} />
              <Route path="query" element={<QueryExplorer />} />
              <Route path="insights" element={<Insights />} />
              <Route path="about" element={<About />} />
            </Route>
          </Routes>
        </Suspense>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
