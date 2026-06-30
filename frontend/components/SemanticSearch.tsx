"use client";

import { useCallback, useState } from "react";

import { searchResume } from "@/lib/api";
import type { SearchResult } from "@/lib/types";

import ResultCard from "./ResultCard";

type SemanticSearchProps = {
  resumeId: string;
};

export default function SemanticSearch({ resumeId }: SemanticSearchProps) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);

  const handleSearch = useCallback(async () => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await searchResume(resumeId, trimmedQuery);
      setSearchResult(result);
    } catch (err) {
      setSearchResult(null);
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setIsLoading(false);
    }
  }, [query, resumeId]);

  return (
    <ResultCard title="Semantic Search">
      <p className="mb-4 text-xs text-slate-400">
        Ask a question about the resume. Top matching chunks are retrieved by
        embedding similarity.
      </p>

      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void handleSearch();
          }}
          placeholder="e.g. What Python experience does the candidate have?"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
        />
        <button
          type="button"
          onClick={() => void handleSearch()}
          disabled={isLoading || !query.trim()}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-600"
        >
          {isLoading ? "Searching..." : "Search"}
        </button>
      </div>

      {error ? (
        <p className="mt-4 rounded-lg border border-red-900/50 bg-red-950/30 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      ) : null}

      {searchResult && searchResult.results.length > 0 ? (
        <ul className="mt-4 space-y-3">
          {searchResult.results.map((hit) => (
            <li
              key={`${hit.chunk_index}-${hit.score}`}
              className="rounded-lg bg-slate-950/60 p-3 ring-1 ring-slate-800"
            >
              <p className="mb-2 text-xs font-medium text-emerald-400">
                Chunk {hit.chunk_index + 1} · score {hit.score.toFixed(4)}
              </p>
              <p className="whitespace-pre-wrap text-xs leading-relaxed text-slate-300">
                {hit.text}
              </p>
            </li>
          ))}
        </ul>
      ) : searchResult ? (
        <p className="mt-4 text-sm text-slate-500">No matching chunks found.</p>
      ) : null}
    </ResultCard>
  );
}
