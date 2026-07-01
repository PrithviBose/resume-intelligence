import ResumeChat from "@/components/ResumeChat";

export default function ChatPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold tracking-tight text-slate-100">
          Resume Chat
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Select a candidate and ask questions about their resume. Answers will
          use semantic search and an LLM once the backend is connected.
        </p>
      </div>

      <ResumeChat />
    </main>
  );
}
