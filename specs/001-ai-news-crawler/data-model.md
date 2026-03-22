# Data Model: AI News Crawler

**Date**: 2026-03-23 | **Branch**: `001-ai-news-crawler`

## Entity Relationship Overview

```
User 1──N Scrap
User 1──N Like
User 1──N Comment
Source 1──N Article
Article 1──N Scrap
Article 1──N Like
Article 1──N Comment
ScoringWeight (singleton config)
CrawlFailure N──1 Source
```

## Entities

### User

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| email | String(255) | UNIQUE, NOT NULL | 로그인 식별자 |
| password_hash | String(255) | NOT NULL | bcrypt 해시 |
| nickname | String(50) | NOT NULL | 표시명 |
| role | String(20) | NOT NULL, default="user" | "admin" \| "user" |
| is_active | Boolean | NOT NULL, default=True | 비활성화 지원 |
| created_at | DateTime | NOT NULL, default=now | |

### Source

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| name | String(200) | NOT NULL | 소스 이름 |
| url | String(2048) | UNIQUE, NOT NULL | |
| type | String(20) | NOT NULL | "rss" \| "scraper" |
| category | String(20) | NOT NULL, default="article" | "article" \| "paper" \| "blog" |
| weight | Float | default=5.0 | 출처 신뢰도 가중치 (1-10) |
| country | String(10) | default="kr" | "kr" \| "global" |
| crawl_interval_hours | Integer | default=24 | |
| is_active | Boolean | default=True | |
| last_crawled_at | DateTime | nullable | |
| last_error | Text | nullable | |

### Article

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| url | String(2048) | UNIQUE, NOT NULL | 원문 URL (중복 판별 1차 기준) |
| title | String(500) | NOT NULL | 제목 (중복 판별 2차 기준) |
| content | Text | nullable | 요약/본문 |
| tags | Text | default="[]" | JSON 배열 (자동 태그) |
| source_id | Integer | FK→sources.id, NOT NULL | |
| category | String(20) | NOT NULL | "article" \| "paper" \| "blog" (소스 카테고리 상속) |
| score | Integer | default=0 | 중요도 점수 |
| score_breakdown | Text | default="{}" | JSON (점수 상세) |
| like_count | Integer | NOT NULL, default=0 | 비정규화 좋아요 수 |
| comment_count | Integer | NOT NULL, default=0 | 비정규화 댓글 수 |
| published_at | DateTime | nullable | |
| crawled_at | DateTime | NOT NULL, default=now | |
| is_deleted | Boolean | NOT NULL, default=False | 소프트 삭제 |

### Scrap

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| user_id | Integer | FK→users.id, NOT NULL | |
| article_id | Integer | FK→articles.id, NOT NULL | |
| created_at | DateTime | NOT NULL, default=now | |

**UNIQUE**: (user_id, article_id)

### Like

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| user_id | Integer | FK→users.id, NOT NULL | |
| article_id | Integer | FK→articles.id, NOT NULL | |
| created_at | DateTime | NOT NULL, default=now | |

**UNIQUE**: (user_id, article_id)
**동기화**: 생성/삭제 시 `articles.like_count` 트랜잭션 내 증감

### Comment

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| user_id | Integer | FK→users.id, NOT NULL | 작성자 |
| article_id | Integer | FK→articles.id, NOT NULL | 대상 게시물 |
| content | Text | NOT NULL | 최대 1000자 |
| is_edited | Boolean | NOT NULL, default=False | |
| created_at | DateTime | NOT NULL, default=now | |
| updated_at | DateTime | nullable | |

**동기화**: 생성/삭제 시 `articles.comment_count` 트랜잭션 내 증감
**삭제 권한**: 본인 또는 관리자

### ScoringWeight

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| key | String(50) | UNIQUE, NOT NULL | "source_trust", "recency", "keyword", "engagement" |
| weight | Float | NOT NULL, default=1.0 | |
| description | String(200) | nullable | |
| updated_at | DateTime | nullable | |

**초기 데이터**: source_trust=1.0, recency=1.0, keyword=1.0, engagement=0.5

### CrawlFailure

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| source_id | Integer | FK→sources.id | |
| url | String(2048) | nullable | None이면 소스 전체 실패 |
| error_message | Text | NOT NULL | |
| failed_at | DateTime | NOT NULL, default=now | |
| retry_count | Integer | default=0 | |
| resolved_at | DateTime | nullable | |
