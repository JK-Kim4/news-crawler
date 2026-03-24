export interface User {
  id: string;
  username: string;
  email: string;
  role: "ADMIN" | "USER";
  created_at: string;
}

export interface Content {
  id: string;
  source_type: "PAPER" | "BLOG" | "NEWS";
  source_name: string;
  title: string;
  original_url: string;
  published_at: string | null;
  author: string | null;
  summary: string | null;
  tags: string[];
  created_at: string;
}

export interface ContentDetail extends Content {
  raw_content: string | null;
}

export interface Bookmark {
  id: string;
  content_id: string;
  content: Content;
  created_at: string;
}

export interface Comment {
  id: string;
  user_id: string;
  username: string;
  content_id: string;
  text: string;
  created_at: string;
}

export interface CrawlStatus {
  is_running: boolean;
  last_crawl_at: string | null;
  next_crawl_at: string | null;
  results: { source_name: string; status: string; count: number }[];
}

export interface DashboardStats {
  total_contents: number;
  contents_today: number;
  total_users: number;
  sources_count: number;
}

export interface Source {
  name: string;
  base_url: string;
  rss_url: string | null;
  selector_title: string;
  selector_content: string;
  language: string;
  source_type: string;
  is_active: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
