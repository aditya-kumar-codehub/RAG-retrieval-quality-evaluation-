import type { Strategy } from "@/lib/api";
import { STRATEGY_LABELS } from "@/lib/api";
import { cn } from "@/lib/utils";

export function StrategyTag({ strategy, className }: { strategy: Strategy; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-[12px] font-medium text-text-secondary", className)}>
      <span className="strategy-dot-3d size-2.5 shrink-0 rounded-full" />
      {STRATEGY_LABELS[strategy]}
    </span>
  );
}
