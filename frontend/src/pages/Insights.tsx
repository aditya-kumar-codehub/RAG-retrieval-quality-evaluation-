import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, SearchX } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { fadeInUp, staggerContainer } from "@/lib/motion";

const FAILURE_CASES = [
  {
    icon: AlertTriangle,
    tone: "critical" as const,
    title: "A real hallucination, caught",
    strategy: "Hybrid",
    body: "Asked about password rotation policy, the model correctly gave the 14-character minimum but then asserted Northwind Cloud enforces periodic rotation — the exact opposite of the source policy. The faithfulness judge flagged the claim unsupported (score 0.50) and separately scored relevance only 2/5, since the answer never actually resolved the yes/no question asked.",
  },
  {
    icon: SearchX,
    tone: "warning" as const,
    title: "A retrieval miss with a lucky save",
    strategy: "BM25",
    body: "For a Pro-tier rate-limit question, retrieval never surfaced the pricing-tiers chunk — a genuine partial miss. The answer came out correct anyway only because rate-limits.md happens to restate the same numbers. Without that redundancy, this exact gap would have produced a hallucinated or unanswerable response.",
  },
  {
    icon: CheckCircle2,
    tone: "neutral" as const,
    title: "A judge failure, not a system failure",
    strategy: "Dense",
    body: "On an uptime-SLA trap question, the model correctly abstained: “I don't have information about that in the provided context.” But the 3B local judge extracted four claims about SLAs that appear nowhere in that answer — pulled from retrieved context instead — and marked them all supported. Rare (1 of 84 pairs), but it means the trap-abstention numbers should be spot-checked, not trusted blindly.",
  },
];

export function Insights() {
  return (
    <div>
      <PageHeader
        eyebrow="Insights"
        title="What the numbers actually mean"
        description="An honest read of the results — including where the evaluation framework itself has limits."
      />

      <motion.div
        initial="hidden"
        animate="visible"
        variants={staggerContainer}
        className="grid grid-cols-1 gap-4 lg:grid-cols-3"
      >
        <motion.div variants={fadeInUp} className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>The headline finding</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-[14px] leading-relaxed text-text-secondary">
                Ranked by NDCG@5 then faithfulness as a tiebreaker, <strong className="text-text-primary">Dense</strong>{" "}
                edges out BM25 and Hybrid on retrieval — but by a razor-thin margin, and{" "}
                <strong className="text-text-primary">Hybrid actually leads on answer relevance</strong> (4.36/5 vs.
                4.14 and 3.68). On a 40-document corpus, the honest conclusion is that all three strategies are roughly
                equivalent: retrieval isn't the bottleneck here. A larger or lexically harder corpus would be needed to
                meaningfully separate BM25 from dense embeddings — the near-tie is itself a useful finding, not a
                non-result.
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeInUp}>
          <Card>
            <CardHeader>
              <CardTitle>Retrieval quality</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-[13.5px] leading-relaxed text-text-secondary">
                Zero non-trap questions had a complete retrieval miss for any strategy. Precision@5 sits around 0.21
                simply because most questions have only 1–2 gold-relevant chunks among the 5 retrieved — a property of
                the eval set, not a retrieval failure.
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeInUp}>
          <Card>
            <CardHeader>
              <CardTitle>Faithfulness</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-[13.5px] leading-relaxed text-text-secondary">
                BM25 and Dense hit 1.00 faithfulness; Hybrid dips to 0.97 with a 7.1% hallucination rate. That's one
                real hallucination in 84 (question, strategy) pairs — see Case 1 below.
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeInUp}>
          <Card>
            <CardHeader>
              <CardTitle>Trap questions</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-[13.5px] leading-relaxed text-text-secondary">
                Dense's 83.3% trap-abstention rate looks like a strategy weakness but isn't — it's a single judge
                artifact (Case 3). BM25 and Hybrid both hit 100% abstention on unanswerable questions.
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      <h2 className="mb-3 mt-8 font-display text-[18px] font-semibold text-text-primary">Example failure cases</h2>
      <motion.div
        initial="hidden"
        animate="visible"
        variants={staggerContainer}
        className="grid grid-cols-1 gap-4 lg:grid-cols-3"
      >
        {FAILURE_CASES.map((c) => (
          <motion.div key={c.title} variants={fadeInUp}>
            <Card
              className={cn(
                "border-t-2",
                c.tone === "critical" && "border-t-status-critical",
                c.tone === "warning" && "border-t-status-warning",
                c.tone === "neutral" && "border-t-border-strong",
              )}
            >
              <CardHeader>
                <div className="flex items-center gap-2">
                  <c.icon
                    className={
                      c.tone === "critical"
                        ? "size-4 text-status-critical"
                        : c.tone === "warning"
                          ? "size-4 text-status-warning"
                          : "size-4 text-text-muted"
                    }
                  />
                  <Badge variant="neutral">{c.strategy}</Badge>
                </div>
                <CardTitle className="mt-1">{c.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-[13px] leading-relaxed text-text-secondary">{c.body}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Known limitations of this evaluation</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-col gap-3 text-[13.5px] leading-relaxed text-text-secondary">
            <li>
              <strong className="text-text-primary">Local judge model noise.</strong> The local judge backend
              (qwen2.5:3b, 3B parameters) occasionally conflates retrieved context with the answer it's supposed to
              be checking during claim extraction on refusal answers — observed in 1 of 84 pairs. For rigorous
              production evaluation, use a full-size judge model via the API backend.
            </li>
            <li>
              <strong className="text-text-primary">One chunk per document.</strong> Given this corpus's document
              lengths, the chunker produces one chunk per document, so "multi-chunk" eval questions are effectively
              multi-document. The chunker does split longer documents — this is a property of this specific
              synthetic corpus.
            </li>
            <li>
              <strong className="text-text-primary">Small corpus.</strong> 40 documents / 28 questions is enough to
              validate the framework and see strategies diverge, not enough for tight statistical confidence. The
              framework scales to larger corpora without code changes.
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
