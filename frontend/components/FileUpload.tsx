"use client";

import { useCallback, useRef, useState } from "react";

import { parseResume } from "@/lib/api";
import type { ParseResult } from "@/lib/types";

const ACCEPTED_TYPES = new Set([
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);

const ACCEPTED_EXTENSIONS = new Set([".pdf", ".docx"]);

type FileUploadProps = {
  onParseComplete: (result: ParseResult) => void;
};

function isAcceptedFile(file: File): boolean {
  const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  return ACCEPTED_TYPES.has(file.type) || ACCEPTED_EXTENSIONS.has(extension);
}

export default function FileUpload({ onParseComplete }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((selected: File | null) => {
    if (!selected || !isAcceptedFile(selected)) return;
    setFile(selected);
    setError(null);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFile(e.dataTransfer.files[0] ?? null);
    },
    [handleFile],
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFile(e.target.files?.[0] ?? null);
    },
    [handleFile],
  );

  const clearFile = useCallback(() => {
    setFile(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  const handleParse = useCallback(async () => {
    if (!file) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await parseResume(file);
      onParseComplete(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to parse resume");
    } finally {
      setIsLoading(false);
    }
  }, [file, onParseComplete]);

  return (
    <div className="space-y-4">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 transition-colors ${
          isDragging
            ? "border-blue-500 bg-blue-950/40"
            : "border-slate-700 bg-slate-900 hover:border-slate-600 hover:bg-slate-800/80"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={onInputChange}
          className="hidden"
        />

        <svg
          className="mb-4 h-10 w-10 text-slate-500"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          aria-hidden
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m6.75 12-3-3m0 0-3 3m3-3v11.25M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H5.25A2.25 2.25 0 0 0 3 3.75v15A2.25 2.25 0 0 0 5.25 21Z"
          />
        </svg>

        {file ? (
          <div className="text-center">
            <p className="text-sm font-medium text-slate-100">{file.name}</p>
            <p className="mt-1 text-xs text-slate-400">
              {(file.size / 1024).toFixed(1)} KB
            </p>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                clearFile();
              }}
              className="mt-3 text-xs font-medium text-blue-400 hover:text-blue-300"
            >
              Remove file
            </button>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-sm font-medium text-slate-200">
              Drag and drop your resume here
            </p>
            <p className="mt-1 text-sm text-slate-400">
              or{" "}
              <span className="font-medium text-blue-400">click to browse</span>
            </p>
            <p className="mt-3 text-xs text-slate-500">PDF or DOCX files</p>
          </div>
        )}
      </div>

      {error ? (
        <p className="rounded-lg border border-red-900/50 bg-red-950/30 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        disabled={!file || isLoading}
        onClick={handleParse}
        className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-600"
      >
        {isLoading ? "Processing..." : "Parse Resume"}
      </button>
    </div>
  );
}
