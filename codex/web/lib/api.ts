import { AdminOverview, ContentItem, NotificationPreference } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

const demoContent: ContentItem[] = [
  {
    id: "demo-1",
    source_name: "Naver D2",
    source_type: "BLOG",
    language: "ko",
    title: "에이전트 워크플로를 운영 환경에 올릴 때 보는 기준",
    original_url: "https://d2.naver.com/demo-1",
    summary: "운영 환경의 에이전트 시스템에서 관측성, 안정성, 비용 제어를 어떻게 잡을지 요약합니다.",
    tags: ["agent", "observability", "ko"],
    published_at: "2026-03-24T09:00:00Z",
    author: "AI Platform Team",
    bookmarked: false,
    raw_content: "에이전트 시스템의 운영 요구사항과 설계 기준을 정리한 예시 본문입니다.",
    comments: [
      {
        id: "comment-1",
        user_id: "u1",
        username: "demo",
        content: "운영 지표 예시가 특히 유용합니다.",
        created_at: "2026-03-24T10:00:00Z",
      },
    ],
  },
  {
    id: "demo-2",
    source_name: "arXiv AI",
    source_type: "PAPER",
    language: "en",
    title: "A Retrieval-Augmented Agent for Long-Horizon Tasks",
    original_url: "https://arxiv.org/abs/demo-2",
    summary: "Long-horizon tasks benefit from retrieval, memory compression, and deterministic tool boundaries.",
    tags: ["retrieval", "memory", "paper"],
    published_at: "2026-03-23T14:00:00Z",
    author: "Research Team",
    bookmarked: true,
    raw_content: "This paper studies retrieval-augmented agent design for long-horizon execution.",
    comments: [],
  },
];

const demoOverview: AdminOverview = {
  total_users: 42,
  total_contents: 128,
  total_sources: 6,
  active_sources: 5,
  last_crawl_status: "SUCCESS",
  last_crawl_at: "2026-03-24T12:00:00Z",
};

const demoNotifications: NotificationPreference = {
  id: "pref-1",
  keywords: ["agent", "llmops", "benchmark"],
  email_enabled: true,
  slack_enabled: false,
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return (await response.json()) as T;
  } catch {
    if (path === "/content") {
      return demoContent as T;
    }
    if (path.startsWith("/content/")) {
      const match = demoContent.find((item) => item.id === path.replace("/content/", ""));
      return (match ?? demoContent[0]) as T;
    }
    if (path === "/me/bookmarks") {
      return demoContent.filter((item) => item.bookmarked) as T;
    }
    if (path === "/admin/overview") {
      return demoOverview as T;
    }
    if (path === "/me/notifications") {
      return demoNotifications as T;
    }
    return [] as T;
  }
}

export function getContents() {
  return request<ContentItem[]>("/content");
}

export function getContent(id: string) {
  return request<ContentItem>(`/content/${id}`);
}

export function getBookmarks() {
  return request<ContentItem[]>("/me/bookmarks");
}

export function getAdminOverview() {
  return request<AdminOverview>("/admin/overview");
}

export function getNotificationPreference() {
  return request<NotificationPreference>("/me/notifications");
}

