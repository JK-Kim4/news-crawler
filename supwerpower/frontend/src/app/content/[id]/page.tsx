"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { ContentDetail } from "@/lib/types";
import TagBadge from "@/components/TagBadge";
import BookmarkButton from "@/components/BookmarkButton";
import CommentSection from "@/components/CommentSection";

function formatFullDate(dateStr: string | null): string {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function sourceTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    PAPER: "논문",
    BLOG: "블로그",
    NEWS: "뉴스",
  };
  return labels[type] || type;
}

export default function ContentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [content, setContent] = useState<ContentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchContent();
  }, [id]);

  async function fetchContent() {
    setLoading(true);
    try {
      const data = await api.get<ContentDetail>(`/contents/${id}`);
      setContent(data);
    } catch {
      setError("콘텐츠를 불러올 수 없습니다.");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-3/4 bg-dark-700 rounded" />
          <div className="flex gap-3">
            <div className="h-6 w-20 bg-dark-700 rounded" />
            <div className="h-6 w-32 bg-dark-700 rounded" />
          </div>
          <div className="card space-y-3">
            <div className="h-4 bg-dark-700 rounded w-full" />
            <div className="h-4 bg-dark-700 rounded w-5/6" />
            <div className="h-4 bg-dark-700 rounded w-4/6" />
          </div>
          <div className="space-y-3">
            <div className="h-4 bg-dark-700 rounded w-full" />
            <div className="h-4 bg-dark-700 rounded w-full" />
            <div className="h-4 bg-dark-700 rounded w-3/4" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
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
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
        <p className="text-gray-500 text-lg mb-4">
          {error || "콘텐츠를 찾을 수 없습니다."}
        </p>
        <Link href="/" className="btn-primary">
          메인으로 돌아가기
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-gray-400 hover:text-gray-200 mb-6 transition-colors"
      >
        <svg
          className="w-4 h-4"
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
        목록으로 돌아가기
      </Link>

      <article>
        <div className="flex items-center gap-3 mb-4">
          <span
            className={`text-xs font-medium px-2.5 py-1 rounded ${
              content.source_type === "PAPER"
                ? "bg-purple-500/20 text-purple-400"
                : content.source_type === "BLOG"
                  ? "bg-green-500/20 text-green-400"
                  : "bg-orange-500/20 text-orange-400"
            }`}
          >
            {sourceTypeLabel(content.source_type)}
          </span>
          <span className="text-sm text-gray-500">{content.source_name}</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4 leading-tight">
          {content.title}
        </h1>

        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400 mb-6">
          {content.author && (
            <span className="flex items-center gap-1">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
              {content.author}
            </span>
          )}
          {content.published_at && (
            <span className="flex items-center gap-1">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              {formatFullDate(content.published_at)}
            </span>
          )}
          <BookmarkButton contentId={content.id} />
        </div>

        {content.summary && (
          <div className="mb-8 p-5 bg-accent-blue/5 border border-accent-blue/20 rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <svg
                className="w-5 h-5 text-accent-blue"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span className="text-sm font-semibold text-accent-blue">
                AI 요약
              </span>
            </div>
            <p className="text-gray-300 leading-relaxed">{content.summary}</p>
          </div>
        )}

        {content.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-8">
            {content.tags.map((tag) => (
              <TagBadge key={tag} tag={tag} />
            ))}
          </div>
        )}

        {content.raw_content && (
          <div className="prose prose-invert max-w-none mb-8">
            <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">
              {content.raw_content}
            </div>
          </div>
        )}

        <div className="flex items-center gap-4 py-6 border-t border-b border-dark-700">
          <a
            href={content.original_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary inline-flex items-center gap-2"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
            원문 보기
          </a>
        </div>
      </article>

      <CommentSection contentId={id} />
    </div>
  );
}
