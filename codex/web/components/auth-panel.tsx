"use client";

import { useState } from "react";

type AuthPanelProps = {
  mode: "login" | "register";
};

export function AuthPanel({ mode }: AuthPanelProps) {
  const [message, setMessage] = useState<string>("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
    const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

    try {
      const response = await fetch(`${baseUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error("Request failed");
      }
      const data = await response.json();
      if (typeof window !== "undefined") {
        window.localStorage.setItem("ai-insights-token", data.access_token);
      }
      setMessage("토큰을 저장했습니다. 관리자 페이지와 개인화 API에서 재사용할 수 있습니다.");
    } catch {
      setMessage("백엔드가 연결되지 않아도 화면 구조는 유지됩니다. API 연결 후 다시 시도하세요.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-4 rounded-[2rem] bg-white p-8 shadow-panel">
      {mode === "register" ? (
        <input name="username" placeholder="username" className="rounded-full border border-ink/10 px-5 py-3" />
      ) : null}
      <input name="email" type="email" placeholder="email" className="rounded-full border border-ink/10 px-5 py-3" />
      <input
        name="password"
        type="password"
        placeholder="password"
        className="rounded-full border border-ink/10 px-5 py-3"
      />
      <button className="rounded-full bg-ink px-5 py-3 text-sm font-semibold text-sand">
        {mode === "login" ? "Sign In" : "Create Account"}
      </button>
      <p className="text-sm text-ink/60">{message}</p>
    </form>
  );
}
