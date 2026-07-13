import type { ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { AnimatedNumber } from "@/components/AnimatedNumber";
import { cn } from "@/lib/utils";

export function StatTile({
  label,
  value,
  countTo,
  hint,
  icon,
  tone = "neutral",
}: {
  label: string;
  /** Static value — used when the tile isn't a plain count (e.g. a strategy name). */
  value?: string;
  /** When set, animates as a counting-up number instead of rendering `value` directly. */
  countTo?: number;
  hint?: string;
  icon?: ReactNode;
  tone?: "neutral" | "good" | "warning" | "critical";
}) {
  const toneClass = {
    neutral: "text-text-primary",
    good: "text-status-good",
    warning: "text-status-warning",
    critical: "text-status-critical",
  }[tone];

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <p className="text-[12px] font-medium text-text-secondary">{label}</p>
        {icon && <span className="text-text-muted">{icon}</span>}
      </div>
      <p className={cn("mt-2 font-display text-[30px] font-semibold leading-none tracking-tight", toneClass)}>
        {countTo !== undefined ? <AnimatedNumber value={countTo} /> : value}
      </p>
      {hint && <p className="mt-2 text-[12px] text-text-muted">{hint}</p>}
    </Card>
  );
}
