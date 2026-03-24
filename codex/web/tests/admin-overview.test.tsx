import React from "react";
import { render, screen } from "@testing-library/react";

import { AdminOverviewPanel } from "@/components/admin-overview";


test("admin overview renders aggregate stats", () => {
  render(
    <AdminOverviewPanel
      overview={{
        total_users: 3,
        total_contents: 10,
        total_sources: 4,
        active_sources: 2,
        last_crawl_status: "SUCCESS",
        last_crawl_at: "2026-03-24T00:00:00Z",
      }}
    />,
  );

  expect(screen.getByText("Users")).toBeInTheDocument();
  expect(screen.getByText("10")).toBeInTheDocument();
  expect(screen.getByText("SUCCESS")).toBeInTheDocument();
});
