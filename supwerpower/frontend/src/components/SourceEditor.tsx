"use client";

import { useState, FormEvent } from "react";
import { Source } from "@/lib/types";

interface SourceEditorProps {
  source?: Source | null;
  onSave: (source: Source) => Promise<void>;
  onCancel: () => void;
}

const SOURCE_TYPES = ["PAPER", "BLOG", "NEWS"];
const LANGUAGES = ["ko", "en", "ja", "zh"];

export default function SourceEditor({
  source,
  onSave,
  onCancel,
}: SourceEditorProps) {
  const [formData, setFormData] = useState<Source>({
    name: source?.name || "",
    base_url: source?.base_url || "",
    rss_url: source?.rss_url || "",
    selector_title: source?.selector_title || "",
    selector_content: source?.selector_content || "",
    language: source?.language || "ko",
    source_type: source?.source_type || "BLOG",
    is_active: source?.is_active ?? true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEditing = !!source;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.base_url.trim()) {
      setError("이름과 기본 URL은 필수입니다.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave({
        ...formData,
        rss_url: formData.rss_url || null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  const updateField = (field: keyof Source, value: string | boolean | null) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="card">
      <h3 className="text-lg font-bold mb-6">
        {isEditing ? "소스 수정" : "새 소스 추가"}
      </h3>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              소스 이름 *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => updateField("name", e.target.value)}
              className="input-field"
              placeholder="예: OpenAI Blog"
              disabled={isEditing}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              기본 URL *
            </label>
            <input
              type="url"
              value={formData.base_url}
              onChange={(e) => updateField("base_url", e.target.value)}
              className="input-field"
              placeholder="https://example.com"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            RSS URL
          </label>
          <input
            type="url"
            value={formData.rss_url || ""}
            onChange={(e) => updateField("rss_url", e.target.value || null)}
            className="input-field"
            placeholder="https://example.com/rss"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              제목 셀렉터
            </label>
            <input
              type="text"
              value={formData.selector_title}
              onChange={(e) => updateField("selector_title", e.target.value)}
              className="input-field"
              placeholder="h1.title"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              콘텐츠 셀렉터
            </label>
            <input
              type="text"
              value={formData.selector_content}
              onChange={(e) => updateField("selector_content", e.target.value)}
              className="input-field"
              placeholder="article.content"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              소스 유형
            </label>
            <select
              value={formData.source_type}
              onChange={(e) => updateField("source_type", e.target.value)}
              className="input-field"
            >
              {SOURCE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type === "PAPER"
                    ? "논문"
                    : type === "BLOG"
                      ? "블로그"
                      : "뉴스"}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              언어
            </label>
            <select
              value={formData.language}
              onChange={(e) => updateField("language", e.target.value)}
              className="input-field"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang} value={lang}>
                  {lang === "ko"
                    ? "한국어"
                    : lang === "en"
                      ? "영어"
                      : lang === "ja"
                        ? "일본어"
                        : "중국어"}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              상태
            </label>
            <div className="flex items-center h-[42px]">
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => updateField("is_active", e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-600 peer-focus:ring-2 peer-focus:ring-accent-blue rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-blue" />
                <span className="ml-3 text-sm text-gray-400">
                  {formData.is_active ? "활성" : "비활성"}
                </span>
              </label>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-dark-700">
          <button type="button" onClick={onCancel} className="btn-secondary">
            취소
          </button>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? "저장 중..." : isEditing ? "수정" : "추가"}
          </button>
        </div>
      </form>
    </div>
  );
}
