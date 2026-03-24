"use client";

import { AuthProvider } from "@/lib/auth";
import Navbar from "@/components/Navbar";
import "@/globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <head>
        <title>AI 인사이트 - AI 뉴스 크롤러</title>
        <meta
          name="description"
          content="최신 AI 논문, 블로그, 뉴스를 한곳에서 확인하세요."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <AuthProvider>
          <Navbar />
          <main>{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
