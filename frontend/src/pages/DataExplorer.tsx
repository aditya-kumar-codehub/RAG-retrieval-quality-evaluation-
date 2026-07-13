import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ChevronDown, Download, Search } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { StrategyTag } from "@/components/StrategyTag";
import { LoadingBlock, ErrorNotice } from "@/components/StateViews";
import { useResults } from "@/lib/queries";
import { STRATEGY_LABELS, type EvalResult, type Strategy } from "@/lib/api";
import { pct } from "@/lib/format";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 10;

export function DataExplorer() {
  const { data, isLoading, isError, error } = useResults();
  const [search, setSearch] = useState("");
  const [strategy, setStrategy] = useState<Strategy | "all">("all");
  const [trapOnly, setTrapOnly] = useState<"all" | "trap" | "answerable">("all");
  const [page, setPage] = useState(0);
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.filter((r) => {
      if (strategy !== "all" && r.strategy !== strategy) return false;
      if (trapOnly === "trap" && !r.is_trap) return false;
      if (trapOnly === "answerable" && r.is_trap) return false;
      if (search && !r.question.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [data, strategy, trapOnly, search]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageRows = filtered.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);

  function resetPage<T>(setter: (v: T) => void) {
    return (v: T) => {
      setter(v);
      setPage(0);
    };
  }

  function downloadCsv() {
    const header = [
      "question_id",
      "question",
      "strategy",
      "difficulty",
      "is_trap",
      "precision_at_5",
      "recall_at_5",
      "ndcg_at_5",
      "mrr",
      "faithfulness_score",
      "has_unsupported_claim",
      "answer_relevance_score",
    ];
    const rows = filtered.map((r) => [
      r.question_id,
      csvEscape(r.question),
      r.strategy,
      r.difficulty,
      r.is_trap,
      r.retrieval_metrics.precision_at_k["5"],
      r.retrieval_metrics.recall_at_k["5"],
      r.retrieval_metrics.ndcg_at_k["5"],
      r.retrieval_metrics.mrr,
      r.faithfulness_score,
      r.has_unsupported_claim,
      r.answer_relevance_score,
    ]);
    const csv = [header.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "rag_eval_results.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <PageHeader
        eyebrow="Data Explorer"
        title="Browse raw results"
        description={`${data?.length ?? 0} rows — every (question, strategy) pair from the evaluation run.`}
        actions={
          <Button variant="secondary" onClick={downloadCsv} disabled={!filtered.length}>
            <Download className="size-4" /> Export CSV
          </Button>
        }
      />

      <Card className="mb-4 flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-text-muted" />
          <Input
            placeholder="Search questions..."
            className="pl-9"
            value={search}
            onChange={(e) => resetPage(setSearch)(e.target.value)}
          />
        </div>
        <Select value={strategy} onValueChange={(v) => resetPage(setStrategy)(v as Strategy | "all")}>
          <SelectTrigger className={cn("w-full sm:w-44", strategy !== "all" && "border-accent/40 text-accent")}>
            <SelectValue placeholder="Strategy" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All strategies</SelectItem>
            <SelectItem value="bm25">BM25</SelectItem>
            <SelectItem value="dense">Dense</SelectItem>
            <SelectItem value="hybrid">Hybrid (RRF)</SelectItem>
          </SelectContent>
        </Select>
        <Select value={trapOnly} onValueChange={(v) => resetPage(setTrapOnly)(v as typeof trapOnly)}>
          <SelectTrigger className={cn("w-full sm:w-44", trapOnly !== "all" && "border-accent/40 text-accent")}>
            <SelectValue placeholder="Question type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All questions</SelectItem>
            <SelectItem value="answerable">Answerable only</SelectItem>
            <SelectItem value="trap">Trap only</SelectItem>
          </SelectContent>
        </Select>
      </Card>

      {isLoading && <LoadingBlock className="h-96" />}
      {isError && <ErrorNotice message={(error as Error).message} />}

      {data && (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] border-collapse text-left text-[13px]">
              <thead>
                <tr className="border-b border-border text-[11px] uppercase tracking-wide text-text-muted">
                  <th className="w-8 px-4 py-3" />
                  <th className="px-2 py-3">Question</th>
                  <th className="px-2 py-3">Strategy</th>
                  <th className="px-2 py-3 text-right">P@5</th>
                  <th className="px-2 py-3 text-right">R@5</th>
                  <th className="px-2 py-3 text-right">NDCG@5</th>
                  <th className="px-2 py-3 text-right">Faithful.</th>
                  <th className="px-2 py-3">Flags</th>
                </tr>
              </thead>
              <tbody>
                {pageRows.map((r) => (
                  <ResultRow
                    key={`${r.question_id}-${r.strategy}`}
                    row={r}
                    isOpen={expanded === `${r.question_id}-${r.strategy}`}
                    onToggle={() =>
                      setExpanded((cur) =>
                        cur === `${r.question_id}-${r.strategy}` ? null : `${r.question_id}-${r.strategy}`,
                      )
                    }
                  />
                ))}
                {pageRows.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-10 text-center text-text-muted">
                      No results match your filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between border-t border-border px-4 py-3 text-[12px] text-text-secondary">
            <span>
              Page {page + 1} of {pageCount} · {filtered.length} rows
            </span>
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                Previous
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={page >= pageCount - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

function ResultRow({ row, isOpen, onToggle }: { row: EvalResult; isOpen: boolean; onToggle: () => void }) {
  return (
    <>
      <tr
        className={cn(
          "cursor-pointer border-b border-border transition-colors hover:bg-surface",
          isOpen && "bg-surface",
        )}
        onClick={onToggle}
      >
        <td className="px-4 py-3 text-text-muted">
          <motion.span
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="inline-flex"
          >
            <ChevronDown className="size-4" />
          </motion.span>
        </td>
        <td className="max-w-[360px] truncate px-2 py-3 text-text-primary">{row.question}</td>
        <td className="px-2 py-3">
          <StrategyTag strategy={row.strategy} />
        </td>
        <td className="px-2 py-3 text-right font-mono text-text-secondary">{pct(row.retrieval_metrics.precision_at_k["5"])}</td>
        <td className="px-2 py-3 text-right font-mono text-text-secondary">{pct(row.retrieval_metrics.recall_at_k["5"])}</td>
        <td className="px-2 py-3 text-right font-mono text-text-secondary">{pct(row.retrieval_metrics.ndcg_at_k["5"])}</td>
        <td className="px-2 py-3 text-right font-mono text-text-secondary">{pct(row.faithfulness_score)}</td>
        <td className="px-2 py-3">
          <div className="flex flex-wrap gap-1">
            {row.is_trap && <Badge variant="warning">Trap</Badge>}
            {row.has_unsupported_claim && <Badge variant="critical">Hallucination</Badge>}
          </div>
        </td>
      </tr>
      {isOpen && (
        <tr className="border-b border-border bg-surface/60">
          <td colSpan={8} className="px-6 py-4">
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            >
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
                  Reference answer
                </p>
                <p className="text-[13px] text-text-secondary">{row.reference_answer}</p>
              </div>
              <div>
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
                  Generated answer ({STRATEGY_LABELS[row.strategy]}, {row.generator_model})
                </p>
                <p className="text-[13px] text-text-secondary">{row.generated_answer}</p>
              </div>
            </div>
            {row.claims.length > 0 && (
              <div className="mt-3">
                <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
                  Claims ({row.claims.length})
                </p>
                <div className="flex flex-col gap-1.5">
                  {row.claims.map((c, i) => (
                    <div key={i} className="flex items-start gap-2 text-[12px]">
                      <Badge
                        variant={
                          c.verdict === "supported" ? "good" : c.verdict === "partial" ? "warning" : "critical"
                        }
                      >
                        {c.verdict}
                      </Badge>
                      <span className="text-text-secondary">{c.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            </motion.div>
          </td>
        </tr>
      )}
    </>
  );
}

function csvEscape(s: string): string {
  return `"${s.replace(/"/g, '""')}"`;
}
