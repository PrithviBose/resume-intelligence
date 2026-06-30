type ResultCardProps = {
  title: string;
  children: React.ReactNode;
};

export default function ResultCard({ title, children }: ResultCardProps) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-lg shadow-black/20">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
        {title}
      </h2>
      <div className="text-sm leading-relaxed text-slate-300">{children}</div>
    </section>
  );
}
