"use client";

import { useState, type ReactNode } from "react";

import type { QueryChainTrace, SearchHit } from "@/lib/types";

type PromptChainStepsProps = {
  chain: QueryChainTrace;
  sources?: SearchHit[];
};

const INTENT_LABELS: Record<QueryChainTrace["step1_understanding"]["intent"], string> = {
  factual: "Factual lookup",
  jd_fit: "JD fit check",
  summary: "Summary",
  other: "Other",
};

const FIT_COLORS: Record<string, string> = {
  strong: "text-emerald-400",
  partial: "text-amber-400",
  weak: "text-red-400",
  unknown: "text-slate-400",
};

function BulletList({ items, emptyText }: { items: string[]; emptyText: string }) {
  if (items.length === 0) {
    return <p className="text-xs italic text-slate-500">{emptyText}</p>;
  }
  return (
    <ul className="list-inside list-disc space-y-0.5 text-xs text-slate-300">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export default function PromptChainSteps({ chain, sources }: PromptChainStepsProps) {
  const [open, setOpen] = useState(true);
  const { step1_understanding, retrieval_chunk_count, step2_evidence } = chain;

  return (
    <div className="mt-2 w-full max-w-[85%]">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 rounded-md border border-blue-500/30 bg-blue-500/10 px-2.5 py-1.5 text-left text-[11px] font-medium text-blue-300 transition-colors hover:border-blue-500/50 hover:bg-blue-500/15"
      >
        <span className="flex items-center gap-1.5">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className={`h-3.5 w-3.5 shrink-0 transition-transform ${open ? "rotate-90" : ""}`}
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M7.21 14.77a.75.75 0 0 1 .02-1.06L11.168 10 7.23 6.29a.75.75 0 1 1 1.04-1.08l4.5 4.25a.75.75 0 0 1 0 1.08l-4.5 4.25a.75.75 0 0 1-1.06-.02Z"
              clipRule="evenodd"
            />
          </svg>
          Prompt chain debug
        </span>
        <span className="text-[10px] font-normal text-blue-300/70">
          {open ? "Hide steps" : "Show steps"}
        </span>
      </button>

      {open ? (
        <div className="mt-2 space-y-2 rounded-lg border border-slate-700/80 bg-slate-900/60 p-3">
          <StepCard
            step={1}
            title="Understand query"
            subtitle="Rewrites your question for search"
          >
            <dl className="space-y-1 text-xs">
              <div>
                <dt className="text-slate-500">Search query</dt>
                <dd className="text-slate-200">{step1_understanding.search_query}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Intent</dt>
                <dd className="text-slate-200">
                  {INTENT_LABELS[step1_understanding.intent]}
                </dd>
              </div>
            </dl>
          </StepCard>

          <StepCard
            step={2}
            title="Retrieve chunks"
            subtitle="Semantic search in Chroma (not LLM)"
          >
            <p className="text-xs text-slate-300">
              {retrieval_chunk_count} chunk{retrieval_chunk_count === 1 ? "" : "s"} retrieved
            </p>
            {sources && sources.length > 0 ? (
              <ul className="mt-1.5 space-y-1">
                {sources.map((hit) => (
                  <li
                    key={hit.chunk_index}
                    className="rounded bg-slate-950/60 px-2 py-1 text-[10px] text-slate-400"
                  >
                    Chunk {hit.chunk_index + 1} · score {hit.score.toFixed(3)}
                  </li>
                ))}
              </ul>
            ) : null}
          </StepCard>

          <StepCard
            step={3}
            title="Analyze evidence"
            subtitle="Extract facts and JD fit from chunks"
          >
            <div className="space-y-2">
              <div>
                <p className="mb-1 text-[10px] font-medium uppercase text-slate-500">
                  Key facts
                </p>
                <BulletList items={step2_evidence.key_facts} emptyText="None found" />
              </div>
              {step2_evidence.matches.length > 0 ? (
                <div>
                  <p className="mb-1 text-[10px] font-medium uppercase text-emerald-600/80">
                    JD matches
                  </p>
                  <BulletList items={step2_evidence.matches} emptyText="None" />
                </div>
              ) : null}
              {step2_evidence.gaps.length > 0 ? (
                <div>
                  <p className="mb-1 text-[10px] font-medium uppercase text-amber-600/80">
                    JD gaps
                  </p>
                  <BulletList items={step2_evidence.gaps} emptyText="None" />
                </div>
              ) : null}
              {step2_evidence.jd_fit ? (
                <p className="text-xs text-slate-400">
                  Fit:{" "}
                  <span className={FIT_COLORS[step2_evidence.jd_fit] ?? "text-slate-300"}>
                    {step2_evidence.jd_fit}
                  </span>
                </p>
              ) : null}
              {step2_evidence.insufficient_context ? (
                <p className="text-xs text-amber-400/90">Insufficient context in excerpts</p>
              ) : null}
            </div>
          </StepCard>

          <StepCard step={4} title="Synthesize answer" subtitle="Final LLM reply (above)">
            <p className="text-xs italic text-slate-500">
              Step 4 uses the evidence from step 3 to write the chat message.
            </p>
          </StepCard>
        </div>
      ) : null}
    </div>
  );
}

function StepCard({
  step,
  title,
  subtitle,
  children,
}: {
  step: number;
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950/40 p-2.5">
      <div className="mb-1.5 flex items-baseline gap-2">
        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-500/15 text-[10px] font-semibold text-blue-400">
          {step}
        </span>
        <div>
          <p className="text-xs font-medium text-slate-200">{title}</p>
          <p className="text-[10px] text-slate-500">{subtitle}</p>
        </div>
      </div>
      {children}
    </div>
  );
}
