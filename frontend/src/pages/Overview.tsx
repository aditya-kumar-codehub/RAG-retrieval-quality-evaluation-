import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowRight, FileText, HelpCircle, Layers, ShieldAlert, Trophy } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { StatTile } from "@/components/StatTile";
import { StrategyTag } from "@/components/StrategyTag";
import { GroupedMetricChart } from "@/components/charts/GroupedMetricChart";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TiltCard } from "@/components/TiltCard";
import { LoadingBlock, LoadingGrid, ErrorNotice } from "@/components/StateViews";
import { useCorpusStats, useSummary } from "@/lib/queries";
import { STRATEGY_LABELS, STRATEGY_ORDER } from "@/lib/api";
import { pct } from "@/lib/format";
import { fadeInUp, staggerContainer } from "@/lib/motion";

export function Overview() {
  const summaryQuery = useSummary();
  const statsQuery = useCorpusStats();

  return (
    <div>
      {/*
        No page-specific hero glow here anymore — the app-wide
        AmbientBackground (mounted in AppShell) now covers every page,
        Overview included. Having both was tried and looked like two
        different design systems stitched together; one consistent
        atmosphere across all pages reads as more premium than a louder
        one-off hero.
      */}
      <PageHeader
        eyebrow="RAG Retrieval Quality Evaluator"
        title="How well does retrieval actually work?"
        description="Real BM25, dense embedding, and hybrid (RRF) retrieval strategies, evaluated on ground-truth retrieval metrics, LLM-as-judge faithfulness, and hallucination detection via trap questions — no vibes, just measured numbers."
        actions={
          <Button asChild variant="primary">
            <Link to="/query">
              Try live retrieval <ArrowRight className="size-4" />
            </Link>
          </Button>
        }
      />

      {statsQuery.isLoading && <LoadingGrid tiles={4} />}
      {statsQuery.isError && <ErrorNotice message={(statsQuery.error as Error).message} />}
      {statsQuery.data && (
        <motion.div
          initial="hidden"
          animate="visible"
          variants={staggerContainer}
          className="grid grid-cols-2 gap-4 lg:grid-cols-4"
        >
          <motion.div variants={fadeInUp}>
            <StatTile
              label="Corpus documents"
              countTo={statsQuery.data.doc_count}
              icon={<FileText className="size-4" />}
              hint="Synthetic internal-docs corpus"
            />
          </motion.div>
          <motion.div variants={fadeInUp}>
            <StatTile
              label="Eval questions"
              countTo={statsQuery.data.question_count}
              icon={<HelpCircle className="size-4" />}
              hint={`${statsQuery.data.single_chunk_count} single-hop · ${statsQuery.data.multi_chunk_count} multi-hop`}
            />
          </motion.div>
          <motion.div variants={fadeInUp}>
            <StatTile
              label="Trap questions"
              countTo={statsQuery.data.trap_count}
              icon={<ShieldAlert className="size-4" />}
              hint="Unanswerable from context"
            />
          </motion.div>
          <motion.div variants={fadeInUp}>
            <StatTile
              label="Best strategy"
              value={summaryQuery.data?.winner ? STRATEGY_LABELS[summaryQuery.data.winner] : "—"}
              icon={<Trophy className="size-4" />}
              hint="By NDCG@5, tie-broken on faithfulness"
              tone="good"
            />
          </motion.div>
        </motion.div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Retrieval quality by strategy</CardTitle>
            <CardDescription>Precision, recall, NDCG, and MRR at k=5, averaged across all 28 eval questions</CardDescription>
          </CardHeader>
          <CardContent>
            {summaryQuery.isLoading && <LoadingBlock />}
            {summaryQuery.isError && <ErrorNotice message={(summaryQuery.error as Error).message} />}
            {summaryQuery.data && (
              <GroupedMetricChart
                valueFormatter={(v) => pct(v)}
                rows={[
                  metricRow("Precision@5", summaryQuery.data, (s) => s.precision_at_5),
                  metricRow("Recall@5", summaryQuery.data, (s) => s.recall_at_5),
                  metricRow("NDCG@5", summaryQuery.data, (s) => s.ndcg_at_5),
                  metricRow("MRR", summaryQuery.data, (s) => s.mrr),
                ]}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Faithfulness &amp; safety</CardTitle>
            <CardDescription>How often the generated answer stays grounded in retrieved context</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {summaryQuery.data &&
              STRATEGY_ORDER.map((s, i) => {
                const row = summaryQuery.data.summary[s];
                return (
                  <motion.div
                    key={s}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + i * 0.08, duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                    className="flex items-center justify-between rounded-[var(--radius-md)] border border-border p-3"
                  >
                    <StrategyTag strategy={s} />
                    <div className="text-right">
                      <p className="font-display text-[15px] font-semibold text-text-primary">
                        {pct(row.faithfulness_score)}
                      </p>
                      <p className="text-[11px] text-text-muted">faithfulness</p>
                    </div>
                  </motion.div>
                );
              })}
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <NextStepCard
          to="/analytics"
          icon={<Layers className="size-4.5" />}
          title="Full analytics"
          description="All five comparison charts across retrieval, faithfulness, and relevance metrics."
        />
        <NextStepCard
          to="/explorer"
          icon={<FileText className="size-4.5" />}
          title="Browse raw results"
          description="Search, filter, and export the full 84-row evaluation dataset."
        />
        <NextStepCard
          to="/query"
          icon={<HelpCircle className="size-4.5" />}
          title="Ask a live question"
          description="Run real retrieval and generation against the corpus, right now."
        />
      </div>
    </div>
  );
}

function metricRow(
  metric: string,
  summary: NonNullable<ReturnType<typeof useSummary>["data"]>,
  pick: (s: (typeof summary.summary)[keyof typeof summary.summary]) => number,
) {
  const row: Record<string, string | number> = { metric };
  for (const s of STRATEGY_ORDER) {
    row[s] = pick(summary.summary[s]);
  }
  return row as { metric: string } & Record<string, number>;
}

function NextStepCard({
  to,
  icon,
  title,
  description,
}: {
  to: string;
  icon: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Link to={to} className="block h-full">
      <TiltCard>
        <Card className="h-full p-5 transition-[box-shadow,border-color] duration-200 hover:border-accent/30 hover:shadow-md">
          <div className="flex size-9 items-center justify-center rounded-[var(--radius-md)] bg-accent/12 text-accent">
            {icon}
          </div>
          <p className="mt-3 font-display text-[14px] font-semibold text-text-primary">{title}</p>
          <p className="mt-1 text-[13px] text-text-secondary">{description}</p>
          <p className="mt-3 flex items-center gap-1 text-[12px] font-medium text-accent opacity-0 transition-opacity group-hover:opacity-100">
            Go <ArrowRight className="size-3" />
          </p>
        </Card>
      </TiltCard>
    </Link>
  );
}
