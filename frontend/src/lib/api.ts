// Thin typed client over the FastAPI backend. Types mirror the plain JSON
// artifacts rag_eval's CLI writes (results.json) and the backend's
// pydantic response models — see backend/app/routers/*.py and
// backend/app/services/data.py.

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type Strategy = "bm25" | "dense" | "hybrid";

export interface RetrievalMetrics {
  precision_at_k: Record<string, number>;
  recall_at_k: Record<string, number>;
  ndcg_at_k: Record<string, number>;
  mrr: number;
}

export type ClaimVerdict = "supported" | "partial" | "unsupported";

export interface Claim {
  text: string;
  verdict: ClaimVerdict;
  supporting_chunk_ids: string[];
}

export interface EvalResult {
  question_id: string;
  question: string;
  difficulty: "easy" | "medium" | "hard";
  is_trap: boolean;
  strategy: Strategy;
  reference_answer: string;
  relevant_chunk_ids: string[];
  retrieved_chunk_ids: string[];
  retrieval_metrics: RetrievalMetrics;
  generated_answer: string;
  generator_model: string;
  faithfulness_score: number;
  has_unsupported_claim: boolean;
  claims: Claim[];
  answer_relevance_score: number;
  answer_relevance_explanation: string;
  context_utilization: number;
  judge_model: string;
}

export interface StrategySummary {
  precision_at_5: number;
  recall_at_5: number;
  ndcg_at_5: number;
  mrr: number;
  faithfulness_score: number;
  hallucination_rate: number;
  answer_relevance_score: number;
  context_utilization: number;
  trap_abstention_rate: number;
}

export interface SummaryResponse {
  summary: Record<Strategy, StrategySummary>;
  winner: Strategy | null;
}

export interface CorpusStats {
  doc_count: number;
  question_count: number;
  single_chunk_count: number;
  multi_chunk_count: number;
  trap_count: number;
}

export interface RetrievedChunk {
  chunk_id: string;
  doc_title: string;
  score: number;
  rank: number;
  text: string;
}

export interface RetrieveResponse {
  question: string;
  strategy: Strategy;
  results: RetrievedChunk[];
}

export interface GenerateResponse {
  question: string;
  strategy: Strategy;
  retrieved: Omit<RetrievedChunk, "text">[];
  answer: string;
  model: string;
  claims: Claim[];
  faithfulness_score: number;
  has_unsupported_claim: boolean;
  answer_relevance_score: number;
  answer_relevance_explanation: string;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),
  runs: () => request<{ runs: string[] }>("/api/runs"),
  results: (run?: string) =>
    request<EvalResult[]>(`/api/results${run ? `?run=${encodeURIComponent(run)}` : ""}`),
  summary: (run?: string) =>
    request<SummaryResponse>(`/api/summary${run ? `?run=${encodeURIComponent(run)}` : ""}`),
  corpusStats: () => request<CorpusStats>("/api/corpus-stats"),
  retrieve: (question: string, strategy: Strategy, k = 5) =>
    request<RetrieveResponse>("/api/retrieve", {
      method: "POST",
      body: JSON.stringify({ question, strategy, k }),
    }),
  generate: (question: string, strategy: Strategy, k = 5) =>
    request<GenerateResponse>("/api/generate", {
      method: "POST",
      body: JSON.stringify({ question, strategy, k }),
    }),
};

export const STRATEGY_LABELS: Record<Strategy, string> = {
  bm25: "BM25",
  dense: "Dense",
  hybrid: "Hybrid (RRF)",
};

export const STRATEGY_ORDER: Strategy[] = ["bm25", "dense", "hybrid"];
