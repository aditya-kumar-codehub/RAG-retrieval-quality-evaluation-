import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Search, AlertCircle, FileSearch, Info } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { StrategyTag } from "@/components/StrategyTag";
import { InlineSpinner } from "@/components/StateViews";
import { useHealth } from "@/lib/queries";
import { api, ApiError, STRATEGY_LABELS, type GenerateResponse, type RetrieveResponse, type Strategy } from "@/lib/api";
import { pct } from "@/lib/format";
import { cn } from "@/lib/utils";
import { staggerContainer, fadeInUp } from "@/lib/motion";

const SAMPLE_QUESTIONS = [
  "What is Northwind Cloud's PTO accrual rate?",
  "How long does the data retention window last for deleted accounts?",
  "What is the refund policy for a mid-cycle downgrade?",
  "Can I get a refund for unused API credits after cancellation?",
];

export function QueryExplorer() {
  const [question, setQuestion] = useState("");
  const [strategy, setStrategy] = useState<Strategy>("bm25");
  const health = useHealth();
  const availableStrategies = health.data?.live_strategies ?? ["bm25", "dense", "hybrid"];
  const isRestricted = health.data && health.data.live_strategies.length < 3;

  useEffect(() => {
    if (health.data && !health.data.live_strategies.includes(strategy)) {
      setStrategy(health.data.live_strategies[0] ?? "bm25");
    }
  }, [health.data, strategy]);

  const retrieveMutation = useMutation({
    mutationFn: () => api.retrieve(question, strategy, 5),
  });
  const generateMutation = useMutation({
    mutationFn: () => api.generate(question, strategy, 5),
  });

  const busy = retrieveMutation.isPending || generateMutation.isPending;

  return (
    <div>
      <PageHeader
        eyebrow="Query Explorer"
        title="Run retrieval and generation live"
        description="Ask a question against the real corpus. Retrieval runs on every request; answer generation is rate-limited since it calls a live LLM."
      />

      {isRestricted && (
        <div className="mb-4 flex items-start gap-2 rounded-[var(--radius-md)] border border-accent/25 bg-accent/8 p-3 text-[12.5px] text-text-secondary">
          <Info className="mt-0.5 size-4 shrink-0 text-accent" />
          <span>
            This public deployment only runs <strong className="text-text-primary">BM25</strong> live — dense and
            hybrid retrieval need an embedding model that doesn't fit this server's free-tier memory. All three
            strategies are still fully compared with real numbers on the{" "}
            <a href="/analytics" className="underline underline-offset-2">
              Analytics
            </a>{" "}
            page, from the saved evaluation run.
          </span>
        </div>
      )}

      <Card className="p-5">
        <div className="flex flex-col gap-3 sm:flex-row">
          <Input
            placeholder="Ask a question about Northwind Cloud's policies..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="flex-1"
            onKeyDown={(e) => {
              if (e.key === "Enter" && question.trim() && !busy) retrieveMutation.mutate();
            }}
          />
          <Select value={strategy} onValueChange={(v) => setStrategy(v as Strategy)}>
            <SelectTrigger className="w-full sm:w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {availableStrategies.map((s) => (
                <SelectItem key={s} value={s}>
                  {STRATEGY_LABELS[s]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {SAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => setQuestion(q)}
              className="rounded-full border border-border-strong px-3 py-1 text-[12px] text-text-secondary transition-[background-color,border-color,transform] duration-150 hover:border-accent/30 hover:bg-surface active:scale-[0.97]"
            >
              {q}
            </button>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Button
            variant="secondary"
            disabled={!question.trim() || busy}
            onClick={() => retrieveMutation.mutate()}
          >
            <Search className="size-4" /> Retrieve only
          </Button>
          <Button disabled={!question.trim() || busy} onClick={() => generateMutation.mutate()}>
            <Sparkles className="size-4" /> Retrieve + generate answer
          </Button>
        </div>
        <p className="mt-2 text-[11px] text-text-muted">
          Answer generation is rate-limited to protect this public demo from cost abuse. If you hit the limit, retrieval-only keeps working.
        </p>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <RetrievalPanel mutation={retrieveMutation} />
        <GenerationPanel mutation={generateMutation} />
      </div>
    </div>
  );
}

function RetrievalPanel({ mutation }: { mutation: ReturnType<typeof useMutation<RetrieveResponse, Error, void>> }) {
  return (
    <Card className={cn("transition-shadow duration-300", mutation.isPending && "shadow-glow")}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSearch className="size-4 text-accent" /> Retrieved chunks
        </CardTitle>
      </CardHeader>
      <CardContent>
        {mutation.isIdle && <EmptyState label="Retrieve to see the top-ranked chunks for your question." />}
        {mutation.isPending && <InlineSpinner label="Retrieving..." />}
        {mutation.isError && <ErrorBanner error={mutation.error} />}
        {mutation.data && (
          <motion.div initial="hidden" animate="visible" variants={staggerContainer} className="flex flex-col gap-3">
            {mutation.data.results.map((r) => (
              <motion.div
                key={r.chunk_id}
                variants={fadeInUp}
                className="rounded-[var(--radius-md)] border border-border bg-surface-raised p-3 transition-colors hover:border-accent/25"
              >
                <div className="mb-1.5 flex items-center justify-between gap-2">
                  <span className="flex items-center gap-2 text-[12px] font-semibold text-text-primary">
                    <span className="flex size-4.5 items-center justify-center rounded-full bg-accent/15 font-mono text-[10px] text-accent">
                      {r.rank}
                    </span>
                    {r.doc_title}
                  </span>
                  <span className="font-mono text-[11px] text-text-muted">score {r.score.toFixed(3)}</span>
                </div>
                <p className="line-clamp-3 text-[12.5px] leading-relaxed text-text-secondary">{r.text}</p>
              </motion.div>
            ))}
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
}

function GenerationPanel({ mutation }: { mutation: ReturnType<typeof useMutation<GenerateResponse, Error, void>> }) {
  return (
    <Card className={cn("transition-shadow duration-300", mutation.isPending && "shadow-glow")}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="size-4 text-accent" /> Generated answer
        </CardTitle>
      </CardHeader>
      <CardContent>
        {mutation.isIdle && <EmptyState label="Generate an answer to see faithfulness and relevance scoring." />}
        {mutation.isPending && <InlineSpinner label="Generating and judging (this can take up to a minute)..." />}
        {mutation.isError && <ErrorBanner error={mutation.error} />}
        <AnimatePresence>
          {mutation.data && (
            <motion.div
              initial="hidden"
              animate="visible"
              variants={staggerContainer}
              className="flex flex-col gap-4"
            >
              <motion.div variants={fadeInUp} className="flex flex-wrap items-center gap-2">
                <StrategyTag strategy={mutation.data.strategy} />
                <Badge variant="neutral">{mutation.data.model}</Badge>
                <Badge variant={mutation.data.has_unsupported_claim ? "critical" : "good"}>
                  faithfulness {pct(mutation.data.faithfulness_score)}
                </Badge>
                <Badge variant="accent">relevance {mutation.data.answer_relevance_score}/5</Badge>
              </motion.div>

              <motion.p
                variants={fadeInUp}
                className="rounded-[var(--radius-md)] border border-border bg-surface p-3.5 text-[13.5px] leading-relaxed text-text-primary"
              >
                {mutation.data.answer}
              </motion.p>

              <motion.div variants={fadeInUp}>
                <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
                  Claims ({mutation.data.claims.length})
                </p>
                <div className="flex flex-col gap-1.5">
                  {mutation.data.claims.map((c, i) => (
                    <div key={i} className="flex items-start gap-2 text-[12.5px]">
                      <Badge
                        variant={c.verdict === "supported" ? "good" : c.verdict === "partial" ? "warning" : "critical"}
                      >
                        {c.verdict}
                      </Badge>
                      <span className="text-text-secondary">{c.text}</span>
                    </div>
                  ))}
                  {mutation.data.claims.length === 0 && (
                    <p className="text-[12.5px] text-text-muted">No factual claims extracted — likely an abstention.</p>
                  )}
                </div>
              </motion.div>

              <motion.p variants={fadeInUp} className="text-[12px] text-text-muted">
                {mutation.data.answer_relevance_explanation}
              </motion.p>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}

function EmptyState({ label }: { label: string }) {
  return <p className="py-8 text-center text-[13px] text-text-muted">{label}</p>;
}

function ErrorBanner({ error }: { error: Error }) {
  let message = error.message;
  if (error instanceof ApiError) {
    if (error.status === 429) {
      message = "Rate limit reached for this demo — please wait a bit and try again.";
    } else if (error.status === 502) {
      message = "The LLM provider is temporarily overloaded (this is on their end, not this demo) — please retry in a few seconds.";
    } else if (error.status === 503) {
      message = "This service is still warming up — please retry in a few seconds.";
    }
  }
  return (
    <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-status-critical/30 bg-status-critical/8 p-3 text-[12.5px] text-status-critical">
      <AlertCircle className="mt-0.5 size-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
