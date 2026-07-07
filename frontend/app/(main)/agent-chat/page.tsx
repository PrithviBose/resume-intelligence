import AgentChat from "@/components/AgentChat";

export default function AgentChatPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold tracking-tight text-slate-100">
          Agentic AI
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          A tool-calling agent answers instead of a fixed pipeline: the LLM decides for itself
          whether and how many times to search the resume before replying, using a{" "}
          <code>search_resume</code> tool.
        </p>
      </div>

      <AgentChat />
    </main>
  );
}
