import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-9 w-full rounded-[var(--radius-md)] border border-border-strong bg-surface-raised px-3 text-[13px] text-text-primary placeholder:text-text-muted outline-none transition-[box-shadow,border-color] duration-150 focus-visible:border-accent/50 focus-visible:shadow-glow",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
