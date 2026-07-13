import type { Strategy } from "@/lib/api";
import { STRATEGY_LABELS } from "@/lib/api";
import { cn } from "@/lib/utils";

const DOT_CLASS: Record<Strategy, string> = {
  bm25: "bg-strategy-bm25",
  dense: "bg-strategy-dense",
  hybrid: "bg-strategy-hybrid",
};

export function StrategyTag({ strategy, className }: { strategy: Strategy; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-[12px] font-medium text-text-secondary", className)}>
      <span className={cn("size-2 rounded-full", DOT_CLASS[strategy])} />
      {STRATEGY_LABELS[strategy]}
    </span>
  );
}

export function strategyColor(strategy: Strategy): string {
  return `var(--color-strategy-${strategy})`;
}
