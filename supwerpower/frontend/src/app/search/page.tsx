"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Content, PaginatedResponse } from "@/lib/types";
import ContentList from "@/components/ContentList";
import SearchBar from "@/components/SearchBar";

function SearchResults() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";

  const [contents, setContents] = useState<Content[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (query) {
      fetchResults();
    }
  }, [query, page]);

  async function fetchResults() {
    setLoading(true);
    try {
      const data = await api.get<PaginatedResponse<Content>>(
        `/contents/search?q=${encodeURIComponent(query)}&page=${page}&size=12`
      );
      setContents(data.items);
      setTotalPages(data.pages);
      setTotal(data.total);
    } catch (err) {
      console.error("검색 실패:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8">
        <div className="max-w-xl mx-auto mb-6">
          <SearchBar initialQuery={query} />
        </div>
        {query && (
          <div className="text-center">
            <h1 className="text-2xl font-bold text-white mb-1">
              &ldquo;{query}&rdquo; 검색 결과
            </h1>
            <p className="text-gray-400 text-sm">
              {loading ? "검색 중..." : `총 ${total}건의 결과`}
            </p>
          </div>
        )}
      </div>

      {!query ? (
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
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <p className="text-gray-500 text-lg">검색어를 입력해주세요</p>
        </div>
      ) : (
        <ContentList
          contents={contents}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
          loading={loading}
        />
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="animate-pulse">
            <div className="max-w-xl mx-auto mb-6">
              <div className="h-10 bg-dark-700 rounded-full" />
            </div>
            <div className="h-8 w-64 bg-dark-700 rounded mx-auto mb-8" />
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
      }
    >
      <SearchResults />
    </Suspense>
  );
}
