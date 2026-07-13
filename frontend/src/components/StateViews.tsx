import { AlertTriangle, Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function LoadingGrid({ tiles = 4 }: { tiles?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {Array.from({ length: tiles }).map((_, i) => (
        <Skeleton key={i} className="h-[100px]" />
      ))}
    </div>
  );
}

export function LoadingBlock({ className = "h-64" }: { className?: string }) {
  return <Skeleton className={className} />;
}

export function InlineSpinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-[13px] text-text-secondary">
      <Loader2 className="size-4 animate-spin" />
      {label}
    </div>
  );
}

export function ErrorNotice({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-[var(--radius-md)] border border-status-critical/25 bg-status-critical/6 p-4 text-[13px]">
      <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-status-critical/15 text-status-critical">
        <AlertTriangle className="size-3.5" />
      </span>
      <div>
        <p className="font-medium text-status-critical">Couldn't load data</p>
        <p className="mt-0.5 text-text-secondary">{message}</p>
      </div>
    </div>
  );
}
