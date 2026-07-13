import { Layers, GitBranch, Server, Cpu, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const PIPELINE_STEPS = [
  { title: "Corpus + eval set", detail: "40 synthetic internal-docs pages, 28 labeled questions (single-hop, multi-hop, trap)." },
  { title: "Retrieval", detail: "BM25 (lexical), dense embeddings (sentence-transformers), and hybrid RRF fusion of both." },
  { title: "Generation", detail: "An LLM answers each question grounded only in its retrieved chunks — local Ollama or Anthropic API, interchangeably." },
  { title: "Judging", detail: "A separate LLM-as-judge pass extracts atomic claims and checks each against the retrieved context (RAGAS-style faithfulness), plus a 1–5 answer-relevance score." },
  { title: "Scoring", detail: "Ground-truth Precision/Recall/NDCG/MRR@k against labeled relevant chunks, plus hallucination rate and trap-question abstention." },
];

const STACK = [
  { icon: Cpu, label: "Core library", items: ["Python 3.11+", "rank-bm25", "sentence-transformers", "numpy / pandas"] },
  { icon: Server, label: "Backend", items: ["FastAPI", "Pydantic", "slowapi rate limiting", "Ollama / Anthropic SDK"] },
  { icon: Layers, label: "Frontend", items: ["React + Vite", "TypeScript", "Tailwind CSS", "Framer Motion", "Recharts"] },
];

export function About() {
  return (
    <div>
      <PageHeader
        eyebrow="About"
        title="A framework, not a chatbot"
        description="This evaluates RAG retrieval quality end-to-end — it doesn't just demo a chat interface over a vector store."
      />

      <Card>
        <CardHeader>
          <CardTitle>Why this exists</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            Most RAG demos show off generation quality and call it a day. This project asks a narrower, more useful
            question: <em>is the retrieval step actually working?</em> It measures retrieval against labeled ground
            truth (not just "the answer looked right"), scores faithfulness with an LLM-as-judge pass that traces
            every claim back to source context, and includes trap questions specifically designed to catch models
            that hallucinate rather than say "I don't know."
          </p>
        </CardContent>
      </Card>

      <h2 className="mb-3 mt-8 font-display text-[18px] font-semibold text-text-primary">Pipeline</h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {PIPELINE_STEPS.map((step, i) => (
          <Card key={step.title} className="p-4">
            <span className="font-mono text-[11px] text-text-muted">{String(i + 1).padStart(2, "0")}</span>
            <p className="mt-1 font-display text-[13.5px] font-semibold text-text-primary">{step.title}</p>
            <p className="mt-1.5 text-[12.5px] leading-relaxed text-text-secondary">{step.detail}</p>
          </Card>
        ))}
      </div>

      <h2 className="mb-3 mt-8 font-display text-[18px] font-semibold text-text-primary">Tech stack</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {STACK.map((s) => (
          <Card key={s.label}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <s.icon className="size-4 text-accent" />
                <CardTitle>{s.label}</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1.5">
                {s.items.map((item) => (
                  <Badge key={item} variant="neutral">
                    {item}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="mt-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-accent" />
            <CardTitle>Public demo safeguards</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-[13.5px] leading-relaxed text-text-secondary">
            The Query Explorer's live answer-generation endpoint calls a real LLM and is rate-limited per visitor to
            keep this public deployment's cost bounded. Retrieval-only queries run against a locally indexed corpus
            (no LLM call) and have a much looser limit. All data shown on the Overview, Analytics, and Data Explorer
            pages comes from a saved, reproducible evaluation run — not live calls.
          </p>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <GitBranch className="size-4 text-accent" />
            <CardTitle>Also available</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-[13.5px] leading-relaxed text-text-secondary">
            A companion Streamlit dashboard covers the same evaluation data with a different UI, and the full
            methodology, corpus design notes, and results writeup live in the project's README.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
