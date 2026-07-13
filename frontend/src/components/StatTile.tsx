import type { ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatTile({
  label,
  value,
  hint,
  icon,
  tone = "neutral",
}: {
  label: string;
  value: string;
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
      <p className={cn("mt-2 font-display text-[28px] font-semibold leading-none", toneClass)}>{value}</p>
      {hint && <p className="mt-2 text-[12px] text-text-muted">{hint}</p>}
    </Card>
  );
}
