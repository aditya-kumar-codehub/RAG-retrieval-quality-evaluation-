import { NavLink, Outlet, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Gauge,
  LineChart,
  Database,
  Search,
  Lightbulb,
  Info,
  Moon,
  Sun,
  Radar,
} from "lucide-react";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: Gauge, end: true },
  { to: "/analytics", label: "Analytics", icon: LineChart },
  { to: "/explorer", label: "Data Explorer", icon: Database },
  { to: "/query", label: "Query Explorer", icon: Search },
  { to: "/insights", label: "Insights", icon: Lightbulb },
  { to: "/about", label: "About", icon: Info },
];

export function AppShell() {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  return (
    <div className="flex min-h-screen bg-background text-text-primary">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-60 flex-col border-r border-border bg-surface lg:flex">
        <div className="flex items-center gap-2.5 px-5 py-6">
          <div className="flex size-8 items-center justify-center rounded-[var(--radius-md)] bg-accent/15">
            <Radar className="size-4.5 text-accent" strokeWidth={2.25} />
          </div>
          <div className="leading-tight">
            <p className="font-display text-[13.5px] font-semibold text-text-primary">RAG Eval</p>
            <p className="text-[11px] text-text-muted">Retrieval Quality</p>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-3">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-2.5 rounded-[var(--radius-md)] px-3 py-2 text-[13px] font-medium transition-colors",
                  isActive
                    ? "bg-accent/12 text-accent"
                    : "text-text-secondary hover:bg-surface-raised hover:text-text-primary",
                )
              }
            >
              <Icon className="size-4" strokeWidth={2} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border p-4">
          <button
            onClick={toggleTheme}
            className="flex w-full items-center justify-between rounded-[var(--radius-md)] border border-border-strong px-3 py-2 text-[12px] font-medium text-text-secondary transition-colors hover:bg-surface-raised"
          >
            <span>{theme === "dark" ? "Dark mode" : "Light mode"}</span>
            {theme === "dark" ? <Moon className="size-3.5" /> : <Sun className="size-3.5" />}
          </button>
        </div>
      </aside>

      <div className="flex min-h-screen w-full flex-col lg:pl-60">
        <MobileTopBar theme={theme} toggleTheme={toggleTheme} />
        <motion.main
          key={location.pathname}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: "easeOut" }}
          className="flex-1 px-4 pb-24 pt-5 sm:px-8 sm:py-8 lg:pb-8"
        >
          <div className="mx-auto w-full max-w-[1400px]">
            <Outlet />
          </div>
        </motion.main>
      </div>

      <MobileTabBar />
    </div>
  );
}

function MobileTopBar({ theme, toggleTheme }: { theme: string; toggleTheme: () => void }) {
  return (
    <div className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-surface/95 px-4 py-3 backdrop-blur lg:hidden">
      <div className="flex items-center gap-2">
        <Radar className="size-4.5 text-accent" />
        <span className="font-display text-[13px] font-semibold">RAG Eval</span>
      </div>
      <button
        onClick={toggleTheme}
        className="flex size-8 items-center justify-center rounded-[var(--radius-md)] border border-border-strong"
      >
        {theme === "dark" ? <Moon className="size-3.5" /> : <Sun className="size-3.5" />}
      </button>
    </div>
  );
}

function MobileTabBar() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex items-stretch justify-around border-t border-border bg-surface/95 backdrop-blur lg:hidden">
      {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              "flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[10px] font-medium",
              isActive ? "text-accent" : "text-text-muted",
            )
          }
        >
          <Icon className="size-4.5" strokeWidth={2} />
          {label.split(" ")[0]}
        </NavLink>
      ))}
    </nav>
  );
}
