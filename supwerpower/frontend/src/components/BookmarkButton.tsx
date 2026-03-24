"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

interface BookmarkButtonProps {
  contentId: string;
  initialBookmarked?: boolean;
  onToggle?: (bookmarked: boolean) => void;
}

export default function BookmarkButton({
  contentId,
  initialBookmarked = false,
  onToggle,
}: BookmarkButtonProps) {
  const { user } = useAuth();
  const [bookmarked, setBookmarked] = useState(initialBookmarked);
  const [loading, setLoading] = useState(false);

  const handleToggle = async () => {
    if (!user) return;
    setLoading(true);
    try {
      if (bookmarked) {
        await api.delete(`/bookmarks/${contentId}`);
        setBookmarked(false);
        onToggle?.(false);
      } else {
        await api.post(`/bookmarks/${contentId}`);
        setBookmarked(true);
        onToggle?.(true);
      }
    } catch (err) {
      console.error("북마크 처리 실패:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className="p-2 rounded-lg hover:bg-dark-700 transition-colors duration-200 disabled:opacity-50"
      title={bookmarked ? "북마크 해제" : "북마크 추가"}
    >
      {bookmarked ? (
        <svg
          className="w-5 h-5 text-accent-blue fill-current"
          viewBox="0 0 24 24"
        >
          <path d="M5 2h14a1 1 0 011 1v19.143a.5.5 0 01-.766.424L12 18.03l-7.234 4.536A.5.5 0 014 22.143V3a1 1 0 011-1z" />
        </svg>
      ) : (
        <svg
          className="w-5 h-5 text-gray-400 hover:text-accent-blue transition-colors"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path d="M5 2h14a1 1 0 011 1v19.143a.5.5 0 01-.766.424L12 18.03l-7.234 4.536A.5.5 0 014 22.143V3a1 1 0 011-1z" />
        </svg>
      )}
    </button>
  );
}
