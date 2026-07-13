import { Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppShell } from "@/components/layout/AppShell";
import { Overview } from "@/pages/Overview";
import { Analytics } from "@/pages/Analytics";
import { DataExplorer } from "@/pages/DataExplorer";
import { QueryExplorer } from "@/pages/QueryExplorer";
import { Insights } from "@/pages/Insights";
import { About } from "@/pages/About";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider delayDuration={150}>
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
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
