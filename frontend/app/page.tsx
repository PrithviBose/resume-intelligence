"use client";

import { useCallback, useState } from "react";

import FileUpload from "@/components/FileUpload";
import Navbar from "@/components/Navbar";
import ResultCard from "@/components/ResultCard";
import SemanticSearch from "@/components/SemanticSearch";
import type { ParseResult } from "@/lib/types";

export default function Home() {
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);

  const handleParseComplete = useCallback((result: ParseResult) => {
    setParseResult(result);
  }, []);

  return (
    <div className="min-h-full bg-slate-950">
      <Navbar />

      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="mb-10">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-100">
            Upload Your Resume
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Upload a PDF or DOCX resume to extract profile details, chunk text,
            and embed it for semantic search.
          </p>
        </div>

        <div className="mb-12 max-w-xl">
          <FileUpload onParseComplete={handleParseComplete} />
        </div>

        <div>
          <h2 className="mb-6 text-lg font-semibold text-slate-100">
            Parse Results
          </h2>

          {!parseResult ? (
            <p className="text-sm text-slate-500">
              Upload a resume and click Parse Resume to see extracted profile,
              text, chunks, and embeddings.
            </p>
          ) : (
            <div className="grid gap-6 md:grid-cols-2">
              <ResultCard title="User Profile">
                <dl className="space-y-2">
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Name
                    </dt>
                    <dd className="text-slate-100">
                      {parseResult.user.user_name ?? "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Email
                    </dt>
                    <dd className="text-slate-100">
                      {parseResult.user.email ?? "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Current Company
                    </dt>
                    <dd className="text-slate-100">
                      {parseResult.user.current_company ?? "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Years of Experience
                    </dt>
                    <dd className="text-slate-100">
                      {parseResult.user.years_of_experience ?? "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      User ID
                    </dt>
                    <dd className="text-slate-300">{parseResult.user.id}</dd>
                  </div>
                </dl>
              </ResultCard>

              <ResultCard title="File Info">
                <dl className="space-y-2">
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Filename
                    </dt>
                    <dd className="text-slate-100">{parseResult.filename}</dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Type
                    </dt>
                    <dd className="uppercase text-slate-100">
                      {parseResult.file_type}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Characters
                    </dt>
                    <dd className="text-slate-100">
                      {parseResult.text_length.toLocaleString()}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Chunks
                    </dt>
                    <dd className="text-slate-100">{parseResult.chunk_count}</dd>
                  </div>
                </dl>
              </ResultCard>

              <ResultCard title="Embeddings">
                <dl className="space-y-2">
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Model
                    </dt>
                    <dd className="text-slate-100">
                      {parseResult.embedding.model_name}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Dimensions
                    </dt>
                    <dd className="text-slate-100">
                      {parseResult.embedding.embedding_dimension}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-500">
                      Resume ID
                    </dt>
                    <dd className="break-all font-mono text-xs text-slate-300">
                      {parseResult.embedding.resume_id}
                    </dd>
                  </div>
                </dl>
              </ResultCard>

              <ResultCard title="Extracted Text">
                <div className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-lg bg-slate-950/60 p-3 text-xs leading-relaxed text-slate-300 ring-1 ring-slate-800">
                  {parseResult.full_text}
                </div>
              </ResultCard>

              <SemanticSearch resumeId={parseResult.embedding.resume_id} />

              <div className="md:col-span-2">
                <ResultCard title="Text Chunks">
                  <ul className="max-h-96 space-y-3 overflow-y-auto">
                    {parseResult.chunks.map((chunk) => (
                      <li
                        key={chunk.index}
                        className="rounded-lg bg-slate-950/60 p-3 ring-1 ring-slate-800"
                      >
                        <p className="mb-2 text-xs font-medium text-blue-400">
                          Chunk {chunk.index + 1}{" "}
                          <span className="font-normal text-slate-500">
                            ({chunk.start_char}–{chunk.end_char})
                          </span>
                        </p>
                        <p className="whitespace-pre-wrap text-xs leading-relaxed text-slate-300">
                          {chunk.text}
                        </p>
                      </li>
                    ))}
                  </ul>
                </ResultCard>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
