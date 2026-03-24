"use client";

import Link from "next/link";
import { Content } from "@/lib/types";
import TagBadge from "./TagBadge";
import BookmarkButton from "./BookmarkButton";

interface ContentCardProps {
  content: Content;
  bookmarked?: boolean;
  onBookmarkToggle?: (contentId: string, bookmarked: boolean) => void;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (hours < 1) return "방금 전";
  if (hours < 24) return `${hours}시간 전`;
  if (days < 7) return `${days}일 전`;
  return date.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function sourceTypeBadge(type: string) {
  const styles: Record<string, string> = {
    PAPER: "bg-purple-500/20 text-purple-400",
    BLOG: "bg-green-500/20 text-green-400",
    NEWS: "bg-orange-500/20 text-orange-400",
  };
  const labels: Record<string, string> = {
    PAPER: "논문",
    BLOG: "블로그",
    NEWS: "뉴스",
  };
  return (
    <span
      className={`text-xs font-medium px-2 py-0.5 rounded ${styles[type] || "bg-gray-500/20 text-gray-400"}`}
    >
      {labels[type] || type}
    </span>
  );
}

export default function ContentCard({
  content,
  bookmarked = false,
  onBookmarkToggle,
}: ContentCardProps) {
  return (
    <div className="card hover:border-dark-600 transition-all duration-200 group flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {sourceTypeBadge(content.source_type)}
          <span className="text-xs text-gray-500">{content.source_name}</span>
        </div>
        <BookmarkButton
          contentId={content.id}
          initialBookmarked={bookmarked}
          onToggle={(b) => onBookmarkToggle?.(content.id, b)}
        />
      </div>

      <Link href={`/content/${content.id}`} className="block flex-1">
        <h3 className="text-lg font-semibold text-gray-100 group-hover:text-accent-blue transition-colors duration-200 mb-2 line-clamp-2">
          {content.title}
        </h3>
        {content.summary && (
          <p className="text-sm text-gray-400 line-clamp-3 mb-4">
            {content.summary}
          </p>
        )}
      </Link>

      <div className="mt-auto pt-4 border-t border-dark-700">
        <div className="flex items-center justify-between">
          <div className="flex flex-wrap gap-1.5">
            {content.tags.slice(0, 3).map((tag) => (
              <TagBadge key={tag} tag={tag} />
            ))}
            {content.tags.length > 3 && (
              <span className="text-xs text-gray-500 self-center">
                +{content.tags.length - 3}
              </span>
            )}
          </div>
          <span className="text-xs text-gray-500 shrink-0 ml-2">
            {formatDate(content.published_at || content.created_at)}
          </span>
        </div>
      </div>
    </div>
  );
}
