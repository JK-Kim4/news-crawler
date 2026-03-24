"use client";

import { Content } from "@/lib/types";
import ContentCard from "./ContentCard";

interface ContentListProps {
  contents: Content[];
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  loading?: boolean;
}

export default function ContentList({
  contents,
  page,
  totalPages,
  onPageChange,
  loading = false,
}: ContentListProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="flex items-center gap-2 mb-3">
              <div className="h-5 w-16 bg-dark-700 rounded" />
              <div className="h-4 w-24 bg-dark-700 rounded" />
            </div>
            <div className="h-6 w-3/4 bg-dark-700 rounded mb-2" />
            <div className="h-4 w-full bg-dark-700 rounded mb-1" />
            <div className="h-4 w-2/3 bg-dark-700 rounded mb-4" />
            <div className="flex gap-2 pt-4 border-t border-dark-700">
              <div className="h-6 w-14 bg-dark-700 rounded-full" />
              <div className="h-6 w-14 bg-dark-700 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (contents.length === 0) {
    return (
      <div className="text-center py-16">
        <svg
          className="w-16 h-16 mx-auto text-gray-600 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p className="text-gray-500 text-lg">콘텐츠가 없습니다</p>
      </div>
    );
  }

  const pageNumbers: number[] = [];
  const maxVisible = 5;
  let start = Math.max(1, page - Math.floor(maxVisible / 2));
  const end = Math.min(totalPages, start + maxVisible - 1);
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1);
  }
  for (let i = start; i <= end; i++) {
    pageNumbers.push(i);
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {contents.map((content) => (
          <ContentCard key={content.id} content={content} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-10">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="p-2 rounded-lg bg-dark-800 border border-dark-700 hover:bg-dark-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>

          {start > 1 && (
            <>
              <button
                onClick={() => onPageChange(1)}
                className="w-10 h-10 rounded-lg bg-dark-800 border border-dark-700 hover:bg-dark-700 text-sm transition-colors"
              >
                1
              </button>
              {start > 2 && (
                <span className="text-gray-500 px-1">...</span>
              )}
            </>
          )}

          {pageNumbers.map((p) => (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${
                p === page
                  ? "bg-accent-blue text-white"
                  : "bg-dark-800 border border-dark-700 hover:bg-dark-700 text-gray-300"
              }`}
            >
              {p}
            </button>
          ))}

          {end < totalPages && (
            <>
              {end < totalPages - 1 && (
                <span className="text-gray-500 px-1">...</span>
              )}
              <button
                onClick={() => onPageChange(totalPages)}
                className="w-10 h-10 rounded-lg bg-dark-800 border border-dark-700 hover:bg-dark-700 text-sm transition-colors"
              >
                {totalPages}
              </button>
            </>
          )}

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="p-2 rounded-lg bg-dark-800 border border-dark-700 hover:bg-dark-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
