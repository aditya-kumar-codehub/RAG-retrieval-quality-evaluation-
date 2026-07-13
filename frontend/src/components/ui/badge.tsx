import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wide ring-1 ring-inset",
  {
    variants: {
      variant: {
        neutral: "bg-surface text-text-secondary ring-border-strong",
        accent: "bg-accent/12 text-accent ring-accent/30",
        good: "bg-status-good/12 text-status-good ring-status-good/30",
        warning: "bg-status-warning/12 text-status-warning ring-status-warning/30",
        critical: "bg-status-critical/12 text-status-critical ring-status-critical/30",
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
