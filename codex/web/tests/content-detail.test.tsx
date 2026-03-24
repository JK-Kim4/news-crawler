import React from "react";
import { render, screen } from "@testing-library/react";

import { ContentDetail } from "@/components/content-detail";


test("content detail renders raw content and comments", () => {
  render(
    <ContentDetail
      item={{
        id: "1",
        source_name: "Naver D2",
        source_type: "BLOG",
        language: "ko",
        title: "운영형 에이전트 설계",
        original_url: "https://example.com/1",
        summary: "핵심 요약",
        tags: ["agent", "ops"],
        published_at: null,
        author: null,
        bookmarked: false,
        raw_content: "원문 본문",
        comments: [
          {
            id: "c1",
            user_id: "u1",
            username: "reviewer",
            content: "좋은 정리입니다.",
            created_at: "2026-03-24T00:00:00Z",
          },
        ],
      }}
    />,
  );

  expect(screen.getByText("운영형 에이전트 설계")).toBeInTheDocument();
  expect(screen.getByText("원문 본문")).toBeInTheDocument();
  expect(screen.getByText("좋은 정리입니다.")).toBeInTheDocument();
});
