"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { DashboardStats, CrawlStatus } from "@/lib/types";
import StatsCard from "@/components/StatsCard";

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleString("ko-KR", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [crawlStatus, setCrawlStatus] = useState<CrawlStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [crawling, setCrawling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [statsData, crawlData] = await Promise.all([
        api.get<DashboardStats>("/admin/stats"),
        api.get<CrawlStatus>("/admin/crawl/status"),
      ]);
      setStats(statsData);
      setCrawlStatus(crawlData);
    } catch {
      setError("데이터를 불러올 수 없습니다.");
    } finally {
      setLoading(false);
    }
  }

  async function runCrawl() {
    setCrawling(true);
    setError(null);
    try {
      const result = await api.post<CrawlStatus>("/admin/crawl/run");
      setCrawlStatus(result);
      const newStats = await api.get<DashboardStats>("/admin/stats");
      setStats(newStats);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "크롤링 실행에 실패했습니다."
      );
    } finally {
      setCrawling(false);
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-8">
        <div className="h-8 w-48 bg-dark-700 rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-dark-700 rounded-xl" />
                <div>
                  <div className="h-4 w-16 bg-dark-700 rounded mb-2" />
                  <div className="h-8 w-12 bg-dark-700 rounded" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-8">관리자 대시보드</h1>

      {error && (
        <div className="mb-6 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <StatsCard
            title="총 콘텐츠"
            value={stats.total_contents.toLocaleString()}
            icon={
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            }
          />
          <StatsCard
            title="오늘 수집"
            value={stats.contents_today.toLocaleString()}
            color="text-green-400"
            icon={
              <svg
                className="w-6 h-6"
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
            }
          />
          <StatsCard
            title="총 사용자"
            value={stats.total_users.toLocaleString()}
            color="text-purple-400"
            icon={
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
                />
              </svg>
            }
          />
          <StatsCard
            title="활성 소스"
            value={stats.sources_count}
            color="text-orange-400"
            icon={
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
            }
          />
        </div>
      )}

      <div className="card mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">크롤링 관리</h2>
          <button
            onClick={runCrawl}
            disabled={crawling || (crawlStatus?.is_running ?? false)}
            className="btn-primary inline-flex items-center gap-2"
          >
            {crawling || crawlStatus?.is_running ? (
              <>
                <svg
                  className="w-4 h-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                크롤링 중...
              </>
            ) : (
              <>
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
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                지금 크롤링 실행
              </>
            )}
          </button>
        </div>

        {crawlStatus && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div className="bg-dark-700 rounded-lg p-4">
              <p className="text-xs text-gray-400 mb-1">상태</p>
              <div className="flex items-center gap-2">
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    crawlStatus.is_running
                      ? "bg-green-400 animate-pulse"
                      : "bg-gray-500"
                  }`}
                />
                <span className="font-medium">
                  {crawlStatus.is_running ? "실행 중" : "대기 중"}
                </span>
              </div>
            </div>
            <div className="bg-dark-700 rounded-lg p-4">
              <p className="text-xs text-gray-400 mb-1">마지막 실행</p>
              <p className="font-medium text-sm">
                {formatDateTime(crawlStatus.last_crawl_at)}
              </p>
            </div>
            <div className="bg-dark-700 rounded-lg p-4">
              <p className="text-xs text-gray-400 mb-1">다음 예약</p>
              <p className="font-medium text-sm">
                {formatDateTime(crawlStatus.next_crawl_at)}
              </p>
            </div>
          </div>
        )}

        {crawlStatus && crawlStatus.results.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">
              크롤링 결과
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-dark-700">
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">
                      소스
                    </th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">
                      상태
                    </th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">
                      수집 수
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {crawlStatus.results.map((result, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-dark-700/50 last:border-0"
                    >
                      <td className="py-3 px-4 text-gray-200">
                        {result.source_name}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded ${
                            result.status === "success"
                              ? "bg-green-500/20 text-green-400"
                              : result.status === "error"
                                ? "bg-red-500/20 text-red-400"
                                : "bg-yellow-500/20 text-yellow-400"
                          }`}
                        >
                          {result.status === "success"
                            ? "성공"
                            : result.status === "error"
                              ? "실패"
                              : "진행 중"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-gray-300">
                        {result.count}건
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
