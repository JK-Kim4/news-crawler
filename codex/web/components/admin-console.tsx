"use client";

import { useState } from "react";

export function AdminConsole() {
  const [message, setMessage] = useState("관리자 토큰을 발급받으면 수동 크롤링을 바로 호출할 수 있습니다.");

  async function triggerCrawl() {
    const token = typeof window !== "undefined" ? window.localStorage.getItem("ai-insights-token") : null;
    const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

    try {
      const response = await fetch(`${baseUrl}/admin/crawl/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({ source_ids: [] }),
      });
      if (!response.ok) {
        throw new Error("Request failed");
      }
      const data = await response.json();
      setMessage(`작업이 큐에 들어갔습니다: ${data.task_id}`);
    } catch {
      setMessage("백엔드 또는 인증 토큰이 준비되지 않았습니다. 그래도 UI와 호출 경로는 연결돼 있습니다.");
    }
  }

  return (
    <div className="rounded-[2rem] bg-white p-8 shadow-panel">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-ink/40">Manual Control</p>
          <h3 className="mt-3 font-display text-3xl text-ink">Run crawl now</h3>
        </div>
        <button onClick={triggerCrawl} className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-sand">
          Trigger
        </button>
      </div>
      <p className="mt-5 text-sm leading-7 text-ink/70">{message}</p>
    </div>
  );
}
