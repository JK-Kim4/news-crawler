"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Source } from "@/lib/types";
import SourceEditor from "@/components/SourceEditor";

export default function AdminSourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    fetchSources();
  }, []);

  async function fetchSources() {
    setLoading(true);
    try {
      const data = await api.get<Source[]>("/admin/sources");
      setSources(data);
    } catch {
      setError("소스 목록을 불러올 수 없습니다.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(source: Source) {
    if (editingSource) {
      await api.put(`/admin/sources/${source.name}`, source);
      setSources((prev) =>
        prev.map((s) => (s.name === source.name ? source : s))
      );
      setEditingSource(null);
    } else {
      await api.post("/admin/sources", source);
      setSources((prev) => [...prev, source]);
      setShowAddForm(false);
    }
  }

  async function toggleActive(name: string, isActive: boolean) {
    try {
      const source = sources.find((s) => s.name === name);
      if (!source) return;
      const updated = { ...source, is_active: !isActive };
      await api.put(`/admin/sources/${name}`, updated);
      setSources((prev) =>
        prev.map((s) =>
          s.name === name ? { ...s, is_active: !isActive } : s
        )
      );
    } catch {
      setError("상태 변경에 실패했습니다.");
    }
  }

  async function deleteSource(name: string) {
    if (!confirm(`"${name}" 소스를 삭제하시겠습니까?`)) return;
    try {
      await api.delete(`/admin/sources/${name}`);
      setSources((prev) => prev.filter((s) => s.name !== name));
    } catch {
      setError("소스 삭제에 실패했습니다.");
    }
  }

  function sourceTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      PAPER: "논문",
      BLOG: "블로그",
      NEWS: "뉴스",
    };
    return labels[type] || type;
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="flex justify-between">
          <div className="h-8 w-32 bg-dark-700 rounded" />
          <div className="h-10 w-32 bg-dark-700 rounded" />
        </div>
        <div className="card">
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="flex items-center gap-4 py-3 border-b border-dark-700 last:border-0"
              >
                <div className="h-4 w-32 bg-dark-700 rounded" />
                <div className="h-4 w-48 bg-dark-700 rounded" />
                <div className="h-4 w-16 bg-dark-700 rounded" />
                <div className="h-4 w-12 bg-dark-700 rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-white">소스 관리</h1>
        {!showAddForm && !editingSource && (
          <button
            onClick={() => setShowAddForm(true)}
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
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
            새 소스 추가
          </button>
        )}
      </div>

      {error && (
        <div className="mb-6 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 text-red-300 hover:text-red-200"
          >
            닫기
          </button>
        </div>
      )}

      {(showAddForm || editingSource) && (
        <div className="mb-8">
          <SourceEditor
            source={editingSource}
            onSave={handleSave}
            onCancel={() => {
              setShowAddForm(false);
              setEditingSource(null);
            }}
          />
        </div>
      )}

      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700 bg-dark-700/30">
                <th className="text-left py-4 px-6 text-gray-400 font-medium">
                  이름
                </th>
                <th className="text-left py-4 px-6 text-gray-400 font-medium">
                  URL
                </th>
                <th className="text-left py-4 px-6 text-gray-400 font-medium">
                  유형
                </th>
                <th className="text-left py-4 px-6 text-gray-400 font-medium">
                  언어
                </th>
                <th className="text-center py-4 px-6 text-gray-400 font-medium">
                  상태
                </th>
                <th className="text-right py-4 px-6 text-gray-400 font-medium">
                  작업
                </th>
              </tr>
            </thead>
            <tbody>
              {sources.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="py-12 text-center text-gray-500"
                  >
                    등록된 소스가 없습니다.
                  </td>
                </tr>
              ) : (
                sources.map((source) => (
                  <tr
                    key={source.name}
                    className="border-b border-dark-700/50 last:border-0 hover:bg-dark-700/20 transition-colors"
                  >
                    <td className="py-4 px-6">
                      <span className="font-medium text-gray-200">
                        {source.name}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <a
                        href={source.base_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-accent-blue hover:text-accent-hover text-xs truncate block max-w-[250px]"
                      >
                        {source.base_url}
                      </a>
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded ${
                          source.source_type === "PAPER"
                            ? "bg-purple-500/20 text-purple-400"
                            : source.source_type === "BLOG"
                              ? "bg-green-500/20 text-green-400"
                              : "bg-orange-500/20 text-orange-400"
                        }`}
                      >
                        {sourceTypeLabel(source.source_type)}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-gray-400 uppercase text-xs">
                      {source.language}
                    </td>
                    <td className="py-4 px-6 text-center">
                      <button
                        onClick={() =>
                          toggleActive(source.name, source.is_active)
                        }
                        className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1 rounded-full transition-colors ${
                          source.is_active
                            ? "bg-green-500/20 text-green-400 hover:bg-green-500/30"
                            : "bg-gray-500/20 text-gray-400 hover:bg-gray-500/30"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            source.is_active ? "bg-green-400" : "bg-gray-500"
                          }`}
                        />
                        {source.is_active ? "활성" : "비활성"}
                      </button>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => {
                            setEditingSource(source);
                            setShowAddForm(false);
                          }}
                          className="p-1.5 rounded hover:bg-dark-600 text-gray-400 hover:text-gray-200 transition-colors"
                          title="수정"
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
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                            />
                          </svg>
                        </button>
                        <button
                          onClick={() => deleteSource(source.name)}
                          className="p-1.5 rounded hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-colors"
                          title="삭제"
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
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
