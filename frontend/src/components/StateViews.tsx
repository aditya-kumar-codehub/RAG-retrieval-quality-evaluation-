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
    <div className="flex items-start gap-3 rounded-[var(--radius-md)] border border-status-critical/30 bg-status-critical/8 p-4 text-[13px] text-status-critical">
      <AlertTriangle className="mt-0.5 size-4 shrink-0" />
      <div>
        <p className="font-medium">Couldn't load data</p>
        <p className="mt-0.5 text-text-secondary">{message}</p>
      </div>
    </div>
  );
}
