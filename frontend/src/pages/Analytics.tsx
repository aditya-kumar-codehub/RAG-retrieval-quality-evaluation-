import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { GroupedMetricChart } from "@/components/charts/GroupedMetricChart";
import { StrategyBarChart } from "@/components/charts/StrategyBarChart";
import { LoadingBlock, ErrorNotice } from "@/components/StateViews";
import { useSummary } from "@/lib/queries";
import { STRATEGY_ORDER, type StrategySummary } from "@/lib/api";
import { pct, num } from "@/lib/format";

export function Analytics() {
  const { data, isLoading, isError, error } = useSummary();

  return (
    <div>
      <PageHeader
        eyebrow="Analytics"
        title="Strategy comparison, five ways"
        description="Every chart is the same 28-question eval set, scored three times — once per retrieval strategy — so the comparison is apples to apples."
      />

      {isLoading && <LoadingBlock className="h-[400px]" />}
      {isError && <ErrorNotice message={(error as Error).message} />}

      {data && (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <Card className="xl:col-span-2">
            <CardHeader>
              <CardTitle>Retrieval quality (Precision, Recall, NDCG, MRR @5)</CardTitle>
              <CardDescription>Ground-truth metrics against labeled relevant chunks — higher is better on all four</CardDescription>
            </CardHeader>
            <CardContent>
              <GroupedMetricChart
                height={300}
                valueFormatter={(v) => pct(v)}
                rows={[
                  row("Precision@5", data, (s) => s.precision_at_5),
                  row("Recall@5", data, (s) => s.recall_at_5),
                  row("NDCG@5", data, (s) => s.ndcg_at_5),
                  row("MRR", data, (s) => s.mrr),
                ]}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Faithfulness score</CardTitle>
              <CardDescription>Share of generated claims the judge model could trace to retrieved context</CardDescription>
            </CardHeader>
            <CardContent>
              <StrategyBarChart
                valueFormatter={(v) => pct(v)}
                domain={[0, 1]}
                data={STRATEGY_ORDER.map((s) => ({ strategy: s, value: data.summary[s].faithfulness_score }))}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Hallucination rate</CardTitle>
              <CardDescription>Share of answers containing at least one unsupported claim — lower is better</CardDescription>
            </CardHeader>
            <CardContent>
              <StrategyBarChart
                valueFormatter={(v) => pct(v)}
                domain={[0, 1]}
                data={STRATEGY_ORDER.map((s) => ({ strategy: s, value: data.summary[s].hallucination_rate }))}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Answer relevance</CardTitle>
              <CardDescription>LLM-judged 1–5 score for whether the answer addresses the question asked</CardDescription>
            </CardHeader>
            <CardContent>
              <StrategyBarChart
                valueFormatter={(v) => num(v, 1)}
                domain={[0, 5]}
                data={STRATEGY_ORDER.map((s) => ({ strategy: s, value: data.summary[s].answer_relevance_score }))}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Trap abstention rate</CardTitle>
              <CardDescription>On unanswerable trap questions, share of runs that correctly declined to answer</CardDescription>
            </CardHeader>
            <CardContent>
              <StrategyBarChart
                valueFormatter={(v) => pct(v)}
                domain={[0, 1]}
                data={STRATEGY_ORDER.map((s) => ({ strategy: s, value: data.summary[s].trap_abstention_rate }))}
              />
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

function row(
  metric: string,
  data: { summary: Record<string, StrategySummary> },
  pick: (s: StrategySummary) => number,
) {
  const r: Record<string, string | number> = { metric };
  for (const s of STRATEGY_ORDER) r[s] = pick(data.summary[s]);
  return r as { metric: string } & Record<string, number>;
}
