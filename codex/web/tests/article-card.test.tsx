import React from "react";
import { render, screen } from "@testing-library/react";

import { ArticleCard } from "@/components/article-card";


test("article card renders title and summary", () => {
  render(
    <ArticleCard
      item={{
        id: "1",
        source_name: "Naver D2",
        source_type: "BLOG",
        language: "ko",
        title: "AI Agent Runtime",
        original_url: "https://example.com/1",
        summary: "요약 본문",
        tags: ["agent"],
        published_at: null,
        author: null,
        bookmarked: false,
      }}
    />,
  );

  expect(screen.getByText("AI Agent Runtime")).toBeInTheDocument();
  expect(screen.getByText("요약 본문")).toBeInTheDocument();
});
