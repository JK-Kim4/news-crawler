"use client";

import { useState, useEffect, FormEvent } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Comment } from "@/lib/types";

interface CommentSectionProps {
  contentId: string;
}

function timeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / (1000 * 60));
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (minutes < 1) return "방금 전";
  if (minutes < 60) return `${minutes}분 전`;
  if (hours < 24) return `${hours}시간 전`;
  if (days < 30) return `${days}일 전`;
  return date.toLocaleDateString("ko-KR");
}

export default function CommentSection({ contentId }: CommentSectionProps) {
  const { user } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadComments();
  }, [contentId]);

  async function loadComments() {
    try {
      setLoading(true);
      const data = await api.get<Comment[]>(
        `/contents/${contentId}/comments`
      );
      setComments(data);
    } catch {
      setError("댓글을 불러올 수 없습니다.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim() || !user) return;

    setSubmitting(true);
    try {
      const comment = await api.post<Comment>(
        `/contents/${contentId}/comments`,
        { text: text.trim() }
      );
      setComments((prev) => [comment, ...prev]);
      setText("");
    } catch {
      setError("댓글 작성에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(commentId: string) {
    try {
      await api.delete(`/comments/${commentId}`);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
    } catch {
      setError("댓글 삭제에 실패했습니다.");
    }
  }

  return (
    <div className="mt-10">
      <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
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
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        댓글 {comments.length > 0 && `(${comments.length})`}
      </h3>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {user ? (
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex gap-3">
            <div className="w-10 h-10 rounded-full bg-accent-blue/20 flex items-center justify-center shrink-0">
              <span className="text-accent-blue font-medium text-sm">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex-1">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="댓글을 작성하세요..."
                rows={3}
                className="input-field resize-none"
              />
              <div className="flex justify-end mt-2">
                <button
                  type="submit"
                  disabled={!text.trim() || submitting}
                  className="btn-primary text-sm"
                >
                  {submitting ? "작성 중..." : "댓글 작성"}
                </button>
              </div>
            </div>
          </div>
        </form>
      ) : (
        <div className="mb-8 p-4 bg-dark-800 rounded-lg border border-dark-700 text-center">
          <p className="text-gray-400">
            댓글을 작성하려면{" "}
            <a href="/login" className="text-accent-blue hover:underline">
              로그인
            </a>
            이 필요합니다.
          </p>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse flex gap-3">
              <div className="w-10 h-10 rounded-full bg-dark-700" />
              <div className="flex-1">
                <div className="h-4 w-24 bg-dark-700 rounded mb-2" />
                <div className="h-4 w-full bg-dark-700 rounded mb-1" />
                <div className="h-4 w-2/3 bg-dark-700 rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : comments.length === 0 ? (
        <p className="text-gray-500 text-center py-8">
          아직 댓글이 없습니다. 첫 번째 댓글을 남겨보세요!
        </p>
      ) : (
        <div className="space-y-6">
          {comments.map((comment) => (
            <div key={comment.id} className="flex gap-3">
              <div className="w-10 h-10 rounded-full bg-dark-700 flex items-center justify-center shrink-0">
                <span className="text-gray-400 font-medium text-sm">
                  {comment.username.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-sm text-gray-200">
                    {comment.username}
                  </span>
                  <span className="text-xs text-gray-500">
                    {timeAgo(comment.created_at)}
                  </span>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                  {comment.text}
                </p>
                {user && user.id === comment.user_id && (
                  <button
                    onClick={() => handleDelete(comment.id)}
                    className="text-xs text-gray-500 hover:text-red-400 mt-1 transition-colors"
                  >
                    삭제
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
