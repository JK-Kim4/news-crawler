"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Content, PaginatedResponse } from "@/lib/types";
import ContentList from "@/components/ContentList";

type SourceTypeFilter = "" | "PAPER" | "BLOG" | "NEWS";

const TABS: { label: string; value: SourceTypeFilter }[] = [
  { label: "전체", value: "" },
  { label: "논문", value: "PAPER" },
  { label: "블로그", value: "BLOG" },
  { label: "뉴스", value: "NEWS" },
];

export default function HomePage() {
  const [contents, setContents] = useState<Content[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sourceType, setSourceType] = useState<SourceTypeFilter>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchContents();
  }, [page, sourceType]);

  async function fetchContents() {
    setLoading(true);
    try {
      let url = `/contents?page=${page}&size=12`;
      if (sourceType) {
        url += `&source_type=${sourceType}`;
      }
      const data = await api.get<PaginatedResponse<Content>>(url);
      setContents(data.items);
      setTotalPages(data.pages);
    } catch (err) {
      console.error("콘텐츠 로딩 실패:", err);
    } finally {
      setLoading(false);
    }
  }

  const handleTabChange = (type: SourceTypeFilter) => {
    setSourceType(type);
    setPage(1);
  };

  return (
    <div>
      <section className="relative overflow-hidden bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900 border-b border-dark-700">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-10 left-10 w-72 h-72 bg-accent-blue/10 rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
            AI 인사이트 허브
          </h1>
          <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto">
            최신 AI 논문, 블로그, 뉴스를 AI가 자동으로 수집하고 요약합니다.
            <br />
            매일 업데이트되는 AI 트렌드를 한눈에 확인하세요.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => handleTabChange(tab.value)}
              className={`px-5 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors duration-200 ${
                sourceType === tab.value
                  ? "bg-accent-blue text-white"
                  : "bg-dark-800 text-gray-400 hover:text-gray-200 hover:bg-dark-700 border border-dark-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <ContentList
          contents={contents}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
          loading={loading}
        />
      </section>
    </div>
  );
}
