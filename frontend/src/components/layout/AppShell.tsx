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
import { AmbientBackground } from "@/components/AmbientBackground";

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
    <div className="flex min-h-screen text-text-primary">
      <AmbientBackground />
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-60 flex-col border-r border-glass-border bg-glass-bg backdrop-blur-xl lg:flex">
        <div className="flex items-center gap-2.5 px-5 py-6">
          <div className="flex size-8 items-center justify-center rounded-[var(--radius-md)] bg-accent/15 shadow-glow">
            <Radar className="size-4.5 text-accent" strokeWidth={2.25} />
          </div>
          <div className="leading-tight">
            <p className="font-display text-[13.5px] font-semibold text-text-primary">RAG Eval</p>
            <p className="text-[11px] text-text-muted">Retrieval Quality</p>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-3">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => {
            const isActive = end ? location.pathname === to : location.pathname.startsWith(to);
            return (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={cn(
                  "group relative flex items-center gap-2.5 rounded-[var(--radius-md)] px-3 py-2 text-[13px] font-medium transition-colors",
                  isActive
                    ? "text-accent"
                    : "text-text-secondary hover:bg-surface-raised hover:text-text-primary",
                )}
              >
                {isActive && (
                  <motion.span
                    layoutId="nav-active-highlight"
                    className="absolute inset-0 rounded-[var(--radius-md)] bg-accent/12 shadow-glow"
                    transition={{ type: "spring", stiffness: 420, damping: 34 }}
                  />
                )}
                <Icon className="relative size-4" strokeWidth={2} />
                <span className="relative">{label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="border-t border-border p-4">
          <button
            onClick={toggleTheme}
            className="flex w-full items-center justify-between rounded-[var(--radius-md)] border border-border-strong px-3 py-2 text-[12px] font-medium text-text-secondary transition-colors hover:bg-surface-raised hover:border-accent/30"
          >
            <span>{theme === "dark" ? "Dark mode" : "Light mode"}</span>
            {theme === "dark" ? <Moon className="size-3.5" /> : <Sun className="size-3.5" />}
          </button>
        </div>
      </aside>

      <div className="relative z-10 flex min-h-screen w-full flex-col lg:pl-60">
        <MobileTopBar theme={theme} toggleTheme={toggleTheme} />
        {/*
          Not using AnimatePresence mode="wait" here: it fully unmounts the
          old page before the new one starts entering, which reads as a lag
          spike on every nav click. Plain key-based remount + a fast fade is
          snappier and doesn't fight with each page's own entrance motion
          (PageHeader, staggered grids, etc. already provide the "arriving"
          feel) — this is just enough to avoid an abrupt cut.
        */}
        <motion.main
          key={location.pathname}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15, ease: "easeOut" }}
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
    <div className="sticky top-0 z-30 flex items-center justify-between border-b border-glass-border bg-glass-bg px-4 py-3 backdrop-blur-xl lg:hidden">
      <div className="flex items-center gap-2">
        <Radar className="size-4.5 text-accent" />
        <span className="font-display text-[13px] font-semibold">RAG Eval</span>
      </div>
      <button
        onClick={toggleTheme}
        className="flex size-8 items-center justify-center rounded-[var(--radius-md)] border border-border-strong transition-colors hover:border-accent/30"
      >
        {theme === "dark" ? <Moon className="size-3.5" /> : <Sun className="size-3.5" />}
      </button>
    </div>
  );
}

function MobileTabBar() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex items-stretch justify-around border-t border-glass-border bg-glass-bg backdrop-blur-xl lg:hidden">
      {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              "flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[10px] font-medium transition-colors",
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
