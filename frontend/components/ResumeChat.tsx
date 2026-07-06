"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchUsers, queryResume } from "@/lib/api";
import type { ChatCandidate, ChatMessage, UserListItem } from "@/lib/types";

import PromptChainSteps from "./PromptChainSteps";
import ResultCard from "./ResultCard";

const SUGGESTED_QUESTIONS = [
  "What is this candidate's strongest technical skill?",
  "Summarize their work experience.",
  "What companies have they worked at?",
  "Do they have leadership or management experience?",
];

function createMessage(
  role: ChatMessage["role"],
  content: string,
  extra?: Pick<ChatMessage, "chain" | "sources">,
): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    timestamp: new Date(),
    ...extra,
  };
}

function formatCandidateLabel(candidate: ChatCandidate): string {
  const name = candidate.userName ?? "Unknown";
  const company = candidate.currentCompany ? ` · ${candidate.currentCompany}` : "";
  return `${name}${company}`;
}

function toChatCandidate(user: UserListItem): ChatCandidate {
  return {
    resumeId: user.resume_id,
    userName: user.user_name,
    email: user.email,
    currentCompany: user.current_company,
  };
}

function MaximizeIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3.5 w-3.5" aria-hidden="true">
      <path d="M13.28 7.78l3.22-3.22v2.69a.75.75 0 0 0 1.5 0v-4.5a.75.75 0 0 0-.75-.75h-4.5a.75.75 0 0 0 0 1.5h2.69l-3.22 3.22a.75.75 0 0 0 1.06 1.06ZM2 17.25v-4.5a.75.75 0 0 1 1.5 0v2.69l3.22-3.22a.75.75 0 0 1 1.06 1.06L4.56 16.5h2.69a.75.75 0 0 1 0 1.5h-4.5a.75.75 0 0 1-.75-.75Z" />
    </svg>
  );
}

function MinimizeIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3.5 w-3.5" aria-hidden="true">
      <path d="M3.28 2.22a.75.75 0 0 0-1.06 1.06L7.44 8.5H4.75a.75.75 0 0 0 0 1.5h4.5A.75.75 0 0 0 10 9.25v-4.5a.75.75 0 0 0-1.5 0v2.69L3.28 2.22ZM13.5 10.75a.75.75 0 0 0 0 1.5h2.69l-5.22 5.22a.75.75 0 1 0 1.06 1.06l5.22-5.22v2.69a.75.75 0 0 0 1.5 0v-4.5a.75.75 0 0 0-.75-.75h-4.5Z" />
    </svg>
  );
}

export default function ResumeChat() {
  const [candidates, setCandidates] = useState<ChatCandidate[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [candidatesLoading, setCandidatesLoading] = useState(true);
  const [candidatesError, setCandidatesError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [maximized, setMaximized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const selectedCandidate =
    candidates.find((c) => c.resumeId === selectedResumeId) ?? null;

  useEffect(() => {
    let cancelled = false;

    async function loadCandidates() {
      setCandidatesLoading(true);
      setCandidatesError(null);

      try {
        const { users } = await fetchUsers();
        if (cancelled) return;

        const nextCandidates = users.map(toChatCandidate);
        setCandidates(nextCandidates);
        setSelectedResumeId(nextCandidates[0]?.resumeId ?? "");
      } catch (error) {
        if (cancelled) return;
        setCandidates([]);
        setSelectedResumeId("");
        setCandidatesError(
          error instanceof Error ? error.message : "Failed to load candidates",
        );
      } finally {
        if (!cancelled) {
          setCandidatesLoading(false);
        }
      }
    }

    void loadCandidates();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Close on Escape key when maximized
  useEffect(() => {
    if (!maximized) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setMaximized(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [maximized]);

  const handleCandidateChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setSelectedResumeId(e.target.value);
      setMessages([]);
      setInput("");
    },
    [],
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading || !selectedCandidate) return;

      const userMessage = createMessage("user", trimmed);
      setMessages((prev) => [...prev, userMessage]);
      setInput("");
      setIsLoading(true);

      try {
        const result = await queryResume(
          selectedCandidate.resumeId,
          trimmed,
          selectedCandidate.userName,
        );
        const assistantMessage = createMessage("assistant", result.answer, {
          chain: result.chain,
          sources: result.sources,
        });
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error) {
        const assistantMessage = createMessage(
          "assistant",
          error instanceof Error
            ? error.message
            : "Something went wrong. Please try again.",
        );
        setMessages((prev) => [...prev, assistantMessage]);
      } finally {
        setIsLoading(false);
        inputRef.current?.focus();
      }
    },
    [isLoading, selectedCandidate],
  );

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      void sendMessage(input);
    },
    [input, sendMessage],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        void sendMessage(input);
      }
    },
    [input, sendMessage],
  );

  const handleSuggestedQuestion = useCallback(
    (question: string) => {
      void sendMessage(question);
    },
    [sendMessage],
  );

  const handleClearChat = useCallback(() => {
    setMessages([]);
    setInput("");
    inputRef.current?.focus();
  }, []);

  const chatDisabled =
    candidatesLoading || !!candidatesError || !selectedCandidate || candidates.length === 0;

  // Shared inner content — used in both normal and maximized views
  const inner = (
    <>
      {/* Candidate selector + controls */}
      <div className="mb-4 space-y-3">
        <p className="text-xs text-slate-400">
          Select a candidate and ask questions about their resume. Answers use
          semantic search over resume chunks and an LLM.
        </p>
        <div>
          <label
            htmlFor="chat-candidate"
            className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500"
          >
            Candidate
          </label>
          {candidatesLoading ? (
            <p className="text-sm text-slate-500">Loading candidates...</p>
          ) : candidatesError ? (
            <p className="text-sm text-red-400">{candidatesError}</p>
          ) : candidates.length === 0 ? (
            <p className="text-sm text-slate-500">
              No candidates available yet. Upload a resume to get started.
            </p>
          ) : (
            <select
              id="chat-candidate"
              value={selectedResumeId}
              onChange={handleCandidateChange}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 focus:border-blue-500 focus:outline-none"
            >
              {candidates.map((candidate) => (
                <option key={candidate.resumeId} value={candidate.resumeId}>
                  {formatCandidateLabel(candidate)}
                </option>
              ))}
            </select>
          )}
          {selectedCandidate ? (
            <p className="mt-2 text-xs text-slate-500">
              {selectedCandidate.email ?? "No email on file"}
              {" · "}
              <span className="font-mono">{selectedCandidate.resumeId.slice(0, 8)}…</span>
            </p>
          ) : null}
        </div>

        {messages.length > 0 ? (
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleClearChat}
              className="rounded-md border border-slate-700 px-2.5 py-1 text-xs text-slate-400 transition-colors hover:border-slate-600 hover:text-slate-200"
            >
              Clear chat
            </button>
          </div>
        ) : null}
      </div>

      {/* Chat box — grows to fill available height when maximized */}
      <div className={`flex flex-col rounded-lg border border-slate-800 bg-slate-950/60 ${maximized ? "min-h-0 flex-1" : "h-[420px]"}`}>
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center px-4 text-center">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/10 ring-1 ring-blue-500/30">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  className="h-5 w-5 text-blue-400"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M8.625 9.75a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm3.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm3.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM8.625 12.75a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm3.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm3.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM4.5 6.75A2.25 2.25 0 0 1 6.75 4.5h10.5A2.25 2.25 0 0 1 19.5 6.75v7.5A2.25 2.25 0 0 1 17.25 16.5H9.6l-3.075 2.05a.75.75 0 0 1-1.175-.62V16.5A2.25 2.25 0 0 1 4.5 14.25v-7.5Z"
                  />
                </svg>
              </div>
              <p className="text-sm font-medium text-slate-200">
                {selectedCandidate
                  ? `Ask anything about ${selectedCandidate.userName ?? "this candidate"}`
                  : "Select a candidate to start chatting"}
              </p>
              <p className="mt-1 max-w-sm text-xs text-slate-500">
                Try a suggested question below, or type your own.
              </p>
              {!chatDisabled ? (
                <div className="mt-5 flex flex-wrap justify-center gap-2">
                  {SUGGESTED_QUESTIONS.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => handleSuggestedQuestion(question)}
                      className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1.5 text-left text-xs text-slate-300 transition-colors hover:border-blue-500/50 hover:bg-blue-500/10 hover:text-slate-100"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex flex-col ${message.role === "user" ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                      message.role === "user"
                        ? "rounded-br-md bg-blue-600 text-white"
                        : "rounded-bl-md bg-slate-800 text-slate-200 ring-1 ring-slate-700"
                    }`}
                  >
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">
                      {message.content}
                    </p>
                    <p
                      className={`mt-1.5 text-[10px] ${
                        message.role === "user" ? "text-blue-200/70" : "text-slate-500"
                      }`}
                    >
                      {message.timestamp.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                  {message.role === "assistant" && message.chain ? (
                    <PromptChainSteps chain={message.chain} sources={message.sources} />
                  ) : null}
                </div>
              ))}

              {isLoading ? (
                <div className="flex justify-start">
                  <div className="rounded-2xl rounded-bl-md bg-slate-800 px-4 py-3 ring-1 ring-slate-700">
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
                    </div>
                  </div>
                </div>
              ) : null}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="border-t border-slate-800 p-3">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder={
                chatDisabled
                  ? "Select a candidate first..."
                  : "Ask about skills, experience, education..."
              }
              disabled={isLoading || chatDisabled}
              className="max-h-32 min-h-[42px] flex-1 resize-none rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim() || chatDisabled}
              className="flex h-[42px] shrink-0 items-center justify-center rounded-lg bg-blue-600 px-4 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-600"
            >
              {isLoading ? (
                <span className="text-xs">Sending...</span>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="h-4 w-4"
                  aria-hidden="true"
                >
                  <path d="M3.478 2.405a.75.75 0 0 0-.926.94l2.787 7.417H13.5a.75.75 0 0 1 0 1.5H5.339l-2.787 7.417a.75.75 0 0 0 .926.94l18-8.5a.75.75 0 0 0 0-1.362l-18-8.5Z" />
                </svg>
              )}
            </button>
          </div>
          <p className="mt-2 text-[10px] text-slate-600">
            {selectedCandidate
              ? `Chatting about ${selectedCandidate.userName ?? "candidate"} · `
              : null}
            Press Enter to send, Shift+Enter for new line
          </p>
        </form>
      </div>
    </>
  );

  // Maximized: full-screen overlay
  if (maximized) {
    return (
      <div className="fixed inset-0 z-50 flex flex-col bg-slate-950 p-6">
        <div className="mb-4 flex shrink-0 items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Resume Chat
          </h2>
          <button
            type="button"
            onClick={() => setMaximized(false)}
            className="flex items-center gap-1.5 rounded-md border border-slate-700 px-2.5 py-1.5 text-xs text-slate-400 transition-colors hover:border-slate-500 hover:text-slate-200"
            aria-label="Minimize chat"
          >
            <MinimizeIcon />
            Minimize
          </button>
        </div>
        <div className="flex min-h-0 flex-1 flex-col text-sm leading-relaxed text-slate-300">
          {inner}
        </div>
      </div>
    );
  }

  // Normal card view with maximize button in header
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-lg shadow-black/20">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Resume Chat
        </h2>
        <button
          type="button"
          onClick={() => setMaximized(true)}
          className="flex items-center gap-1.5 rounded-md border border-slate-700 px-2.5 py-1.5 text-xs text-slate-400 transition-colors hover:border-slate-500 hover:text-slate-200"
          aria-label="Maximize chat"
        >
          <MaximizeIcon />
          Maximize
        </button>
      </div>
      <div className="text-sm leading-relaxed text-slate-300">{inner}</div>
    </section>
  );
}
