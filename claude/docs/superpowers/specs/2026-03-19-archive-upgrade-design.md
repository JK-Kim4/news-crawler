# AI 아카이브 고도화 설계 문서

**날짜**: 2026-03-19
**작성자**: Claude (브레인스토밍 기반)
**대상 프로젝트**: `ai-news-crawler`

---

## 개요

개인용 AI 기술 아카이브 서비스로 고도화한다. 단순 뉴스 피드에서 벗어나 크롤링 결과를 체계적으로 아카이빙하고 관리할 수 있는 서비스로 확장한다.

핵심 변경 사항:
1. **소스 국가 분류**: sources.json에 `country` 필드 추가, 한국/해외 탭 필터링
2. **소스 대폭 확충**: 한국 10개, 해외 7개 기술 블로그 신규 추가
3. **아카이빙 기능**: 북마크, 메모, 커스텀 태그 (UserNote 별도 테이블)
4. **전문 검색**: SQLite FTS5 기반 제목+본문 검색
5. **온디맨드 번역**: 해외 아티클 상세 페이지에서 무료 한글 번역 (deep-translator)
6. **UI 전면 재설계**: Tailwind CSS + 사이드바 레이아웃

---

## 1. 데이터 모델

### 1.1 Source 변경

`country` 필드 추가. 기존 `Source` 모델의 레거시 `Column()` 스타일에 맞춰 동일하게 구현:

```python
country = Column(String(10), default="global", nullable=False)  # "kr" | "global"
```

### 1.2 UserNote 신규 테이블

Article과 1:1 관계이나 별도 테이블로 분리 (멀티유저/멀티프로필 등 향후 확장 고려).
기존 모델(Source, Article, CrawlFailure)의 레거시 `Column()` 스타일에 맞춰 동일 스타일로 구현:

```python
class UserNote(Base):
    __tablename__ = "user_notes"

    id            = Column(Integer, primary_key=True)
    article_id    = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_bookmarked = Column(Boolean, default=False, nullable=False)
    memo          = Column(Text, nullable=True)
    user_tags     = Column(Text, default="[]", nullable=False)  # JSON array string
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
```

- `article_id`에 UNIQUE 제약으로 1:1 보장
- Article 삭제 시 CASCADE로 UserNote도 삭제

### 1.3 ArticleFTS 가상 테이블 (SQLite FTS5)

별도 DDL로 생성 (SQLAlchemy ORM 외부). trigram tokenizer로 한국어 substring 검색 지원:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS article_fts
USING fts5(
  title, content,
  content='articles',
  content_rowid='id',
  tokenize='trigram'
);
```

- `content='articles'` external content 모드: 원문은 articles 테이블에, FTS는 인덱스만 보관
- trigram tokenizer: 한국어 포함 임의 부분 문자열 검색 지원 (SQLite 3.38+ 필요)
- 검색 쿼리: `SELECT rowid FROM article_fts WHERE article_fts MATCH ?`
- 파이프라인에서 Article 저장 후 수동 INSERT로 동기화 (트리거 미사용)

---

## 2. 소스 확충

### 2.1 sources.json 스키마 변경

```json
{
  "name": "string",
  "url": "string",
  "type": "rss" | "scraper",
  "weight": 1-10,
  "country": "kr" | "global"
}
```

### 2.2 신규 한국 소스 (country: "kr")

| 소스 | URL | 타입 | 가중치 |
|------|-----|------|--------|
| 컬리 Tech | `https://helloworld.kurly.com/feed.xml` | rss | 7 |
| 뱅크샐러드 | `https://blog.banksalad.com/rss.xml` | rss | 7 |
| 카카오페이 Tech | `https://tech.kakaopay.com/rss.xml` | rss | 7 |
| 카카오엔터프라이즈 | `https://tech.kakaoenterprise.com/feed` | rss | 7 |
| 데브시스터즈 | `https://tech.devsisters.com/rss.xml` | rss | 6 |
| 라인 Tech | `https://techblog.lycorp.co.jp/ko/feed/index` | rss | 7 |
| 당근 Tech | `https://medium.com/feed/daangn` | rss | 7 |
| 쿠팡 Engineering | `https://medium.com/feed/coupang-engineering` | rss | 7 |
| 무신사 Tech | `https://medium.com/feed/musinsa-tech` | rss | 6 |
| 하이퍼커넥트 | `https://hyperconnect.github.io/feed.xml` | rss | 6 |

### 2.3 신규 해외 소스 (country: "global")

| 소스 | URL | 타입 | 가중치 |
|------|-----|------|--------|
| Google DeepMind | `https://deepmind.com/blog/feed/basic/` | rss | 9 |
| Microsoft Research | `https://www.microsoft.com/en-us/research/feed/` | rss | 8 |
| NVIDIA Developer (AI) | `https://developer.nvidia.com/blog/feed` | rss | 8 |
| ByteByteGo | `https://blog.bytebytego.com/feed` | rss | 7 |
| Uber Engineering AI | `https://eng.uber.com/category/articles/ai/feed` | rss | 7 |
| IEEE Spectrum AI | `https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss` | rss | 7 |
| Interconnects | `https://www.interconnects.ai/feed` | rss | 7 |

### 2.4 기존 소스 country 필드 추가

기존 소스에 `country` 필드 추가 (쏘카는 현재 sources.json에 없으므로 신규 추가):
- 한국(`"kr"`): 카카오 Tech Blog, 네이버 D2, 토스, 우아한형제들 + 쏘카(신규 추가, `https://tech.socarcorp.kr/feed`)
- 해외(`"global"`): ArXiv AI, ArXiv ML, OpenAI, Anthropic, Google AI, HuggingFace, Meta AI, Netflix, Hacker News

**loader.py 수정 필요**: Source 생성/업데이트 코드에 `country` 필드 반영. 단, `required_fields`에 `country`를 추가하면 기존 sources.json을 먼저 업데이트하지 않은 상태에서 앱 시작 시 `SourceConfigError`로 crash 발생. **구현 순서**: sources.json 업데이트 → loader.py required_fields 추가. 또는 `country`를 optional 필드(누락 시 `"global"` 기본값)로 처리하는 방식도 가능.

**선택 방식**: country는 optional 필드로 처리 (required_fields에 포함하지 않음). 누락 시 `"global"` 기본값. 이렇게 하면 sources.json 업데이트 순서에 무관하게 안전하게 동작한다.

---

## 3. 아카이빙 기능

### 3.1 북마크

- `UserNote.is_bookmarked` 토글
- 피드 카드에 북마크 버튼 (HTMX partial update)
- `/bookmarks` 페이지에서 북마크된 아티클만 조회

### 3.2 메모

- `UserNote.memo` 텍스트 저장
- 아티클 카드에 메모 미리보기 (첫 50자)
- HTMX로 인라인 편집 (textarea → 저장)

### 3.3 커스텀 태그

- `UserNote.user_tags` JSON 배열 (`["태그1", "태그2"]`)
- 자동 태그(Article.tags)와 구분: 자동은 파란색, 커스텀은 노란색
- 콤마 구분 입력 방식
- 커스텀 태그로 필터링하는 기능은 **v2 범위** (현재는 표시만)

### 3.4 온디맨드 번역

- 대상: `Source.country == "global"` 아티클의 상세 페이지. 한국 아티클에 번역 요청 시 HTTP 400 반환
- 버튼: "한글 요약 보기" 클릭 시 HTMX 요청
- 번역 범위: **제목 + 본문 앞 500자** (요지 파악용, 전문 번역 아님)
- 엔진: `deep-translator` GoogleTranslator (무료, API 키 불필요)
- 결과: 페이지 내 별도 영역에 표시, DB 저장 없음 (매번 요청)
- 에러 처리: 타임아웃 5초, 네트워크/서비스 오류 무관하게 "번역을 가져올 수 없습니다" 단일 메시지 표시

---

## 4. 전문 검색 (FTS5)

### 4.1 검색 대상

- `article_fts` 가상 테이블 (title + content)
- 검색 파라미터: `?q=검색어&country=kr|global|all`

### 4.2 검색 API

```
GET /search?q=rag&country=kr
```

응답: 검색 결과 아티클 목록 (최대 50건), 관련도 순 정렬

### 4.3 FTS 동기화

**신규 Article 동기화 (`process_item()` 내)**:
- Article DB 저장(`db.commit()`) 후 raw SQL로 FTS INSERT
- FTS INSERT 실패 시 예외를 catch하여 로그만 남기고 진행 (Article 저장은 이미 commit됨, 검색 누락은 허용)
- 구현:
  ```python
  try:
      db.execute(text("INSERT INTO article_fts(rowid, title, content) VALUES (:id, :title, :content)"),
                 {"id": article.id, "title": article.title, "content": article.content})
      db.commit()
  except Exception as e:
      logger.warning("FTS insert failed for article %s: %s", article.id, e)
  ```

**초기 배포 시 기존 데이터 인덱싱 (`init_db()` 내)**:
- FTS5 `INSERT OR IGNORE`는 지원되지 않으므로, 테이블 생성 후 `rebuild` 명령 사용:
  ```python
  db.execute(text("INSERT INTO article_fts(article_fts) VALUES('rebuild')"))
  ```
- `rebuild`는 `content='articles'` 설정을 기반으로 articles 테이블 전체를 재인덱싱하며 멱등성 보장

- 재빌드 수동 실행 필요 시에도 동일 `rebuild` 명령 사용

---

## 5. UI 재설계

### 5.1 CSS 프레임워크

- Pico CSS → **Tailwind CSS Play CDN** (`https://cdn.tailwindcss.com`) 교체
- 커스텀 설정 없이 기본 유틸리티 클래스만 사용 (빌드 불필요)
- HTMX 유지 (부분 업데이트)

### 5.2 레이아웃 구조

```
┌─────────────────────────────────────────────┐
│ [사이드바 220px] │ [메인 영역]               │
│                  │ ┌─[헤더]────────────────┐ │
│ AI Archive       │ │ 피드  전체|한국|해외   │ │
│                  │ │ 검색바          정렬   │ │
│ 📰 피드   [12]   │ └───────────────────────┘ │
│ 🔖 북마크        │ ┌─[피드]────────────────┐ │
│ 🔍 검색          │ │ [아티클 카드]         │ │
│                  │ │ [아티클 카드]         │ │
│ ─────────        │ │ ...                   │ │
│ 📡 소스 관리     │ └───────────────────────┘ │
│                  │                           │
│ ─────────        │                           │
│ 마지막: 2시간 전 │                           │
│ [지금 크롤링]    │                           │
└─────────────────────────────────────────────┘
```

### 5.3 페이지별 구성

**피드 (`/`)**
- 헤더: 전체/한국/해외 탭, 검색바(빠른 검색), 스코어/최신 정렬
- 아티클 카드: 제목(링크), 스코어 배지(컬러), 소스명+국가 플래그+시간, 자동태그+커스텀태그, 북마크/메모/읽음 액션, 메모 미리보기

**북마크 (`/bookmarks`)**
- 북마크된 아티클 목록 (피드와 동일한 카드 컴포넌트)
- 메모가 있는 경우 우선 표시

**검색 (`/search`)**
- 검색창 + 국가 필터
- FTS5 결과 목록

**소스 관리 (`/sources`)**
- 소스 목록 테이블 (국가 필드 포함)
- 활성/비활성 토글, 실패 재시도

### 5.4 아티클 카드 컴포넌트

```
┌─────────────────────────────────────────────┐
│ LLM Fine-tuning 최신 트렌드 분석        [92점]│ ← 스코어 컬러 (90+파랑, 70+초록, 기타보라)
│ HuggingFace · 🌏 해외 · 2시간 전            │
│ [llm] [fine-tuning] [📌 꼭읽기]             │ ← 자동태그 파랑, 커스텀 노랑
│ 📝 "LoRA 관련 내용 중요..."                 │ ← 메모 미리보기
│ [🔖 북마크] [📝 메모] [✓ 읽음] [원문 →]    │
└─────────────────────────────────────────────┘
```

---

## 6. 신규 API 엔드포인트

```
GET  /bookmarks                    — 북마크 목록 페이지
GET  /search?q=&country=           — 전문 검색 페이지
POST /articles/{id}/bookmark       — 북마크 토글 (HTMX), 응답: 토글된 버튼 HTML
POST /articles/{id}/memo           — 메모 저장/수정 (HTMX), Body: form field `memo=...`
POST /articles/{id}/tags           — 커스텀 태그 저장 (HTMX), Body: form field `user_tags=태그1,태그2`
                                     (콤마 구분 문자열 → 파싱하여 JSON 배열로 저장)
POST /articles/{id}/translate      — 온디맨드 번역 (HTMX, 해외만), kr 아티클은 HTTP 400
```

기존 엔드포인트 유지:
```
GET  /articles/{id}                — 아티클 상세 페이지
POST /articles/{id}/read           — 읽음 토글 (HTMX)
GET  /sources                      — 소스 관리 페이지
POST /sources/{id}/toggle          — 소스 활성/비활성 (HTMX)
POST /sources/{id}/retry           — 소스 재시도 (HTMX)
POST /api/crawl                    — 수동 크롤링 트리거
```

---

## 7. 의존성 추가

```toml
[project.dependencies]
deep-translator = ">=1.11.0"   # 온디맨드 번역
```

---

## 8. 마이그레이션 고려사항

- `user_notes` 테이블: `create_all()`로 자동 생성
- `article_fts` 가상 테이블: SQLAlchemy 외부 DDL로 `init_db()` 내 별도 실행
- `sources.country` 컬럼: **`create_all()`은 기존 테이블에 컬럼을 추가하지 않음**. SQLite는 `ALTER TABLE ADD COLUMN IF NOT EXISTS`를 지원하지 않으므로 `init_db()` 내에서 try/except로 처리:
  ```python
  try:
      db.execute(text("ALTER TABLE sources ADD COLUMN country TEXT DEFAULT 'global'"))
      db.commit()
  except Exception:
      pass  # 컬럼이 이미 존재하는 경우 무시
  ```
- 기존 커스텀 태그(`Article.tags`)는 자동 태그이므로 UserNote.user_tags와 별개로 유지
- 기존 엔드포인트(`POST /articles/{id}/read`, `POST /sources/{id}/toggle` 등)는 변경 없이 유지

---

## 9. 구현 범위 외 (v2 이후)

- 멀티유저 지원
- AI 기반 자동 요약 (API 비용 발생)
- 뉴스레터 발송
- 모바일 앱
