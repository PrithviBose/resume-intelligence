"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchUsers } from "@/lib/api";
import type { ChatCandidate, ChatMessage, UserListItem } from "@/lib/types";

import ResultCard from "./ResultCard";

const SUGGESTED_QUESTIONS = [
  "What is this candidate's strongest technical skill?",
  "Summarize their work experience.",
  "What companies have they worked at?",
  "Do they have leadership or management experience?",
];

function createMessage(role: ChatMessage["role"], content: string): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    timestamp: new Date(),
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

function mockAssistantReply(question: string, candidate?: ChatCandidate | null): string {
  const name = candidate?.userName ?? "the selected candidate";
  return (
    `This is a preview response for: "${question}"\n\n` +
    `Once the chat API is connected, answers about ${name}'s resume will be generated ` +
    `using retrieved resume context and an LLM.`
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

      // UI-only placeholder until the chat API is wired up.
      await new Promise((resolve) => setTimeout(resolve, 900));

      const assistantMessage = createMessage(
        "assistant",
        mockAssistantReply(trimmed, selectedCandidate),
      );
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
      inputRef.current?.focus();
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
  return (
    <ResultCard title="Resume Chat">
      <div className="mb-4 space-y-4">
        <p className="text-xs text-slate-400">
          Select a candidate and ask questions about their resume. Answers will
          use semantic search + LLM once the backend is connected.
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
          ) : (            <select
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
              <span className="font-mono">
                {selectedCandidate.resumeId.slice(0, 8)}…
              </span>
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

      <div className="flex h-[420px] flex-col rounded-lg border border-slate-800 bg-slate-950/60">
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
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
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
                        message.role === "user"
                          ? "text-blue-200/70"
                          : "text-slate-500"
                      }`}
                    >
                      {message.timestamp.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
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
    </ResultCard>
  );
}
