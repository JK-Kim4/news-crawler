# API Endpoints: AI News Crawler

**Date**: 2026-03-22 | **Branch**: `001-ai-news-crawler`

## Authentication

기존 인증 엔드포인트를 유지한다 (`/auth/*`).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | - | 회원가입 |
| POST | /auth/login | - | 로그인 |
| POST | /auth/logout | login | 로그아웃 |
| GET | /auth/verify | - | 이메일 인증 |
| POST | /auth/forgot-password | - | 비밀번호 재설정 요청 |
| POST | /auth/reset-password | - | 비밀번호 재설정 |

## Articles (게시물)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /articles | - | 게시물 목록 (중요도 순, 페이지네이션) |
| GET | /articles/{id} | - | 게시물 상세 |
| GET | /articles/search | - | 게시물 검색 (제목/요약 기반) |

### Query Parameters (GET /articles)

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | 페이지 번호 |
| size | int | 20 | 페이지 크기 |
| category | string | null | 필터: "article" \| "paper" \| "blog" |
| sort | string | "score" | 정렬: "score" \| "date" |

### Query Parameters (GET /articles/search)

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| q | string | required | 검색 키워드 |
| page | int | 1 | 페이지 번호 |
| size | int | 20 | 페이지 크기 |
| category | string | null | 카테고리 필터 |

## Likes (좋아요)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /articles/{id}/like | login | 좋아요 토글 (있으면 삭제, 없으면 생성) |

**Response**: `{ "liked": bool, "like_count": int }`

## Comments (댓글)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /articles/{id}/comments | - | 댓글 목록 (작성순) |
| POST | /articles/{id}/comments | login | 댓글 작성 |
| PUT | /comments/{id} | login (본인) | 댓글 수정 |
| DELETE | /comments/{id} | login (본인 또는 admin) | 댓글 삭제 |

### Request Body (POST /articles/{id}/comments)

```json
{ "content": "string (1~1000자)" }
```

### Request Body (PUT /comments/{id})

```json
{ "content": "string (1~1000자)" }
```

## Scraps (스크랩)

기존 bookmark 엔드포인트를 활용/확장한다.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /articles/{id}/scrap | login | 스크랩 토글 |
| GET | /my/scraps | login | 내 스크랩 목록 (최신순) |

**Response (POST)**: `{ "scrapped": bool }`

### Query Parameters (GET /my/scraps)

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | 페이지 번호 |
| size | int | 20 | 페이지 크기 |

## Admin - Sources (관리자: 크롤링 소스)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /admin/sources | admin | 소스 목록 |
| POST | /admin/sources | admin | 소스 추가 |
| PUT | /admin/sources/{id} | admin | 소스 수정 |
| DELETE | /admin/sources/{id} | admin | 소스 삭제 |
| POST | /admin/sources/{id}/crawl | admin | 즉시 크롤링 실행 |

### Request Body (POST/PUT /admin/sources)

```json
{
  "name": "string",
  "url": "string",
  "type": "rss | scraper",
  "category": "article | paper | blog",
  "weight": 1.0,
  "country": "kr | global",
  "crawl_interval_hours": 24,
  "is_active": true
}
```

## Admin - Articles (관리자: 게시물 관리)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| DELETE | /admin/articles/{id} | admin | 게시물 소프트 삭제 |
| PUT | /admin/articles/{id}/score | admin | 중요도 점수 수동 조정 |

### Request Body (PUT /admin/articles/{id}/score)

```json
{ "score": 85.5 }
```

## Admin - Users (관리자: 사용자 관리)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /admin/users | admin | 사용자 목록 |
| PUT | /admin/users/{id}/role | admin | 역할 변경 |
| PUT | /admin/users/{id}/active | admin | 활성/비활성화 |

### Request Body (PUT /admin/users/{id}/role)

```json
{ "role": "admin | user" }
```

### Request Body (PUT /admin/users/{id}/active)

```json
{ "is_active": true | false }
```

## Admin - Scoring (관리자: 가중치 관리)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /admin/scoring-weights | admin | 가중치 목록 |
| PUT | /admin/scoring-weights/{key} | admin | 가중치 수정 |

### Request Body (PUT /admin/scoring-weights/{key})

```json
{ "weight": 1.5 }
```

## Admin - Alerts (관리자: 크롤링 실패 알림)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /admin/crawl-failures | admin | 미해결 크롤링 실패 목록 |
| GET | /admin/crawl-failures/count | admin | 미해결 실패 건수 (알림 배지용) |
| PUT | /admin/crawl-failures/{id}/resolve | admin | 실패 건 해결 처리 |

## Common Response Patterns

### Paginated List Response

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

### Error Response

```json
{
  "detail": "error message"
}
```

**HTTP Status Codes**:
- 200: 성공
- 201: 생성 성공
- 400: 잘못된 요청
- 401: 인증 필요
- 403: 권한 없음
- 404: 리소스 없음
- 422: 유효성 검증 실패
