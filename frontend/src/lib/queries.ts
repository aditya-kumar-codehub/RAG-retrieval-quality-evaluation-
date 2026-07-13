import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useRuns() {
  return useQuery({ queryKey: ["runs"], queryFn: api.runs });
}

export function useResults(run?: string) {
  return useQuery({ queryKey: ["results", run ?? "latest"], queryFn: () => api.results(run) });
}

export function useSummary(run?: string) {
  return useQuery({ queryKey: ["summary", run ?? "latest"], queryFn: () => api.summary(run) });
}

export function useCorpusStats() {
  return useQuery({ queryKey: ["corpus-stats"], queryFn: api.corpusStats });
}

export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: api.health, staleTime: 60 * 1000 });
}
