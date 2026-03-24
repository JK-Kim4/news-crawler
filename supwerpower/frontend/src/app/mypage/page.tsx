"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Bookmark } from "@/lib/types";
import TagBadge from "@/components/TagBadge";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function MyPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      fetchBookmarks();
    }
  }, [user]);

  async function fetchBookmarks() {
    setLoading(true);
    try {
      const data = await api.get<Bookmark[]>("/bookmarks");
      setBookmarks(data);
    } catch {
      setError("북마크를 불러올 수 없습니다.");
    } finally {
      setLoading(false);
    }
  }

  async function removeBookmark(contentId: string) {
    try {
      await api.delete(`/bookmarks/${contentId}`);
      setBookmarks((prev) => prev.filter((b) => b.content_id !== contentId));
    } catch {
      setError("북마크 삭제에 실패했습니다.");
    }
  }

  if (authLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="animate-pulse">
          <div className="h-8 w-48 bg-dark-700 rounded mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="card animate-pulse">
                <div className="h-6 w-3/4 bg-dark-700 rounded mb-3" />
                <div className="h-4 w-full bg-dark-700 rounded mb-2" />
                <div className="h-4 w-2/3 bg-dark-700 rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">마이페이지</h1>
          <p className="text-gray-400">
            {user.username}님의 북마크 목록
          </p>
        </div>
        <div className="text-right text-sm text-gray-500">
          <p>{user.email}</p>
          <p>가입일: {formatDate(user.created_at)}</p>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-6 w-3/4 bg-dark-700 rounded mb-3" />
              <div className="h-4 w-full bg-dark-700 rounded mb-2" />
              <div className="h-4 w-2/3 bg-dark-700 rounded" />
            </div>
          ))}
        </div>
      ) : bookmarks.length === 0 ? (
        <div className="text-center py-20">
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
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
          <p className="text-gray-500 text-lg mb-4">
            아직 북마크한 콘텐츠가 없습니다.
          </p>
          <Link href="/" className="btn-primary">
            콘텐츠 둘러보기
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {bookmarks.map((bookmark) => (
            <div
              key={bookmark.id}
              className="card hover:border-dark-600 transition-all duration-200 group flex flex-col"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded ${
                      bookmark.content.source_type === "PAPER"
                        ? "bg-purple-500/20 text-purple-400"
                        : bookmark.content.source_type === "BLOG"
                          ? "bg-green-500/20 text-green-400"
                          : "bg-orange-500/20 text-orange-400"
                    }`}
                  >
                    {bookmark.content.source_type === "PAPER"
                      ? "논문"
                      : bookmark.content.source_type === "BLOG"
                        ? "블로그"
                        : "뉴스"}
                  </span>
                  <span className="text-xs text-gray-500">
                    {bookmark.content.source_name}
                  </span>
                </div>
                <button
                  onClick={() => removeBookmark(bookmark.content_id)}
                  className="p-2 rounded-lg hover:bg-dark-700 transition-colors text-accent-blue"
                  title="북마크 해제"
                >
                  <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                    <path d="M5 2h14a1 1 0 011 1v19.143a.5.5 0 01-.766.424L12 18.03l-7.234 4.536A.5.5 0 014 22.143V3a1 1 0 011-1z" />
                  </svg>
                </button>
              </div>

              <Link
                href={`/content/${bookmark.content.id}`}
                className="block flex-1"
              >
                <h3 className="text-lg font-semibold text-gray-100 group-hover:text-accent-blue transition-colors duration-200 mb-2 line-clamp-2">
                  {bookmark.content.title}
                </h3>
                {bookmark.content.summary && (
                  <p className="text-sm text-gray-400 line-clamp-3 mb-4">
                    {bookmark.content.summary}
                  </p>
                )}
              </Link>

              <div className="mt-auto pt-4 border-t border-dark-700">
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1.5">
                    {bookmark.content.tags.slice(0, 3).map((tag) => (
                      <TagBadge key={tag} tag={tag} />
                    ))}
                  </div>
                  <span className="text-xs text-gray-500 shrink-0 ml-2">
                    {formatDate(
                      bookmark.content.published_at ||
                        bookmark.content.created_at
                    )}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
