export type ContentItem = {
  id: string;
  source_name: string;
  source_type: string;
  language: string;
  title: string;
  original_url: string;
  summary: string;
  tags: string[];
  published_at: string | null;
  author: string | null;
  bookmarked: boolean;
  raw_content?: string | null;
  comments?: CommentItem[];
};

export type CommentItem = {
  id: string;
  user_id: string;
  username: string;
  content: string;
  created_at: string;
};

export type AdminOverview = {
  total_users: number;
  total_contents: number;
  total_sources: number;
  active_sources: number;
  last_crawl_status: string | null;
  last_crawl_at: string | null;
};

export type NotificationPreference = {
  id: string;
  keywords: string[];
  email_enabled: boolean;
  slack_enabled: boolean;
};

