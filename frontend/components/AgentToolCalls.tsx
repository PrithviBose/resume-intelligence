"use client";

import { useState } from "react";

import type { AgentToolCall } from "@/lib/types";

type AgentToolCallsProps = {
  toolCalls: AgentToolCall[];
};

export default function AgentToolCalls({ toolCalls }: AgentToolCallsProps) {
  const [open, setOpen] = useState(true);

  return (
    <div className="mt-2 w-full max-w-[85%]">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 rounded-md border border-purple-500/30 bg-purple-500/10 px-2.5 py-1.5 text-left text-[11px] font-medium text-purple-300 transition-colors hover:border-purple-500/50 hover:bg-purple-500/15"
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
          Agent trace{toolCalls.length > 0 ? ` — ${toolCalls.length} tool call${toolCalls.length === 1 ? "" : "s"}` : ""}
        </span>
        <span className="text-[10px] font-normal text-purple-300/70">
          {open ? "Hide steps" : "Show steps"}
        </span>
      </button>

      {open ? (
        <div className="mt-2 space-y-2 rounded-lg border border-slate-700/80 bg-slate-900/60 p-3">
          {toolCalls.length === 0 ? (
            <p className="text-xs italic text-slate-500">
              The agent answered directly, without calling any tool.
            </p>
          ) : (
            toolCalls.map((call, index) => (
              <div
                key={`${call.tool_name}-${index}`}
                className="rounded-md border border-slate-800 bg-slate-950/40 p-2.5"
              >
                <div className="mb-1.5 flex items-baseline gap-2">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-purple-500/15 text-[10px] font-semibold text-purple-400">
                    {index + 1}
                  </span>
                  <div>
                    <p className="text-xs font-medium text-slate-200">{call.tool_name}</p>
                    <p className="text-[10px] text-slate-500">
                      The agent chose this tool — it wasn&apos;t a fixed step
                    </p>
                  </div>
                </div>
                <dl className="space-y-1 text-xs">
                  {Object.keys(call.arguments).length > 0 ? (
                    <div>
                      <dt className="text-slate-500">Arguments the agent chose</dt>
                      <dd className="text-slate-200">
                        {Object.entries(call.arguments)
                          .map(([key, value]) => `${key}: ${value}`)
                          .join(" · ")}
                      </dd>
                    </div>
                  ) : null}
                  <div>
                    <dt className="text-slate-500">Result</dt>
                    <dd className="text-slate-200">{call.result_summary}</dd>
                  </div>
                </dl>
              </div>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
