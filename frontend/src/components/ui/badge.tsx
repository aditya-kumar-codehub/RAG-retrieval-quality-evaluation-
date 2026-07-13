import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wide",
  {
    variants: {
      variant: {
        neutral: "border-border-strong bg-surface text-text-secondary",
        accent: "border-transparent bg-accent/15 text-accent",
        good: "border-transparent bg-status-good/15 text-status-good",
        warning: "border-transparent bg-status-warning/15 text-status-warning",
        critical: "border-transparent bg-status-critical/15 text-status-critical",
      },
    },
    defaultVariants: { variant: "neutral" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />;
}
