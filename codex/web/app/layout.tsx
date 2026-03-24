import type { Metadata } from "next";

import "@/app/globals.css";
import { TopNav } from "@/components/top-nav";

export const metadata: Metadata = {
  title: "AI Insight Ledger",
  description: "Korean-first AI research and engineering insight feed",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <TopNav />
        <main className="mx-auto flex min-h-[calc(100vh-84px)] max-w-6xl flex-col gap-8 px-6 py-8">{children}</main>
      </body>
    </html>
  );
}

