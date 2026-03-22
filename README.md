# AI News Crawler — Claude vs Gemini 구현 비교

> AI 기술 블로그 아카이브 서비스를 **Claude**와 **Gemini** 두 AI로 각각 구현하여 코드 품질, 설계 방식, 개발 경험을 비교하는 프로젝트입니다.

---

## 프로젝트 개요

단순 뉴스 피드를 넘어, AI 관련 기술 블로그 글을 **크롤링 → 스코어링 → 아카이빙**하는 개인 기술 아카이브 서비스입니다.

### 주요 기능

| 기능 | 설명 |
|------|------|
| 크롤링 | RSS / 스크래퍼 기반 기술 블로그 31개 소스 수집 |
| 스코어링 | 출처 가중치 · 최신성 · AI 키워드 매칭으로 0~100점 산출 |
| 국가 필터 | 한국(🇰🇷) / 해외(🌏) 소스 분류 및 탭 필터링 |
| 북마크 | 아티클 북마크 저장 및 북마크 전용 피드 |
| 메모 | 아티클별 개인 메모 작성 |
| 커스텀 태그 | 아티클에 사용자 정의 태그 추가 |
| 전문 검색 | SQLite FTS5 + trigram tokenizer 기반 한/영 검색 |
| 번역 | 해외 아티클 제목/본문 온디맨드 한글 번역 (deep-translator) |
| 자동 크롤링 | APScheduler 기반 주기적 자동 수집 |

---

## 디렉토리 구조

```
.
├── claude/          # Claude로 구현한 버전
├── codex/           # Codex로 구현한 버전
└── gemini/          # Gemini로 구현한 버전 (예정)
```

---

## Claude 구현체 (`claude/`)

### 기술 스택

- **Backend:** FastAPI + SQLAlchemy 2.0 + SQLite
- **Crawler:** httpx + feedparser + BeautifulSoup4
- **Scheduler:** APScheduler
- **Search:** SQLite FTS5 (trigram tokenizer)
- **Translation:** deep-translator (GoogleTranslator, 무료)
- **Frontend:** Jinja2 + HTMX + Tailwind CSS (Play CDN)

### 소스 목록 (31개)

**해외 (16개)**
ArXiv AI/ML, OpenAI Blog, Anthropic Blog, Google AI Blog, Google DeepMind, HuggingFace Blog, Microsoft Research, NVIDIA Developer, Meta AI Blog, Netflix Tech Blog, ByteByteGo, Uber Engineering, IEEE Spectrum AI, Interconnects, Hacker News AI

**한국 (15개)**
Naver D2, Kakao Tech Blog, Toss Tech Blog, 우아한형제들 기술 블로그, Socar Tech Blog, Kurly Tech Blog, Banksalad Tech Blog, KakaoPay Tech Blog, Kakao Enterprise, Line Tech Blog, 당근 Tech Blog, Coupang Engineering, Devsisters Tech Blog, Musinsa Tech Blog, Hyperconnect Tech

### 실행 방법

```bash
cd claude

# 의존성 설치
pip install -e .

# 서버 실행
uvicorn main:app --reload --port 8000
```

브라우저에서 http://localhost:8000 접속

### 화면 구성

```
┌─────────────────────────────────────────────────────┐
│  AI Archive    │  피드                               │
│  AI 기술 아카이브 │  [전체] [🇰🇷 한국] [🌏 해외]          │
│                │                                    │
│  메뉴          │  ┌─ 아티클 카드 ──────────────────┐ │
│  📰 피드       │  │ 제목                   [92점]  │ │
│  🔖 북마크     │  │ HuggingFace Blog · 🌏 · 2시간전│ │
│  🔍 검색       │  │ [llm] [fine-tuning]            │ │
│               │  │ 📝 "메모 추가"                   │ │
│  관리          │  │ [☆ 북마크] [+태그] [✓ 읽음] [원문]│ │
│  📡 소스 관리  │  └─────────────────────────────────┘ │
│               │                                    │
│  ⟳ 지금 크롤링 │  ...                               │
└─────────────────────────────────────────────────────┘
```

### DB 스키마

```
sources          articles         user_notes
───────────      ───────────      ───────────
id               id               id
name             source_id (FK)   article_id (FK, UNIQUE)
url              url              is_bookmarked
type             title            memo
weight           content          user_tags (JSON)
country          score            created_at
is_active        tags (JSON)      updated_at
last_crawled_at  published_at
                 is_read
                 score_breakdown

article_fts (FTS5 virtual table)
─────────────────────────────────
title, content
content='articles', tokenize='trigram'
```

### 테스트

```bash
cd claude
python -m pytest tests/ -v
```

42개 테스트, 전체 통과

---

## Codex 구현체 (`codex/`)

Codex 버전도 동일한 요구사항을 기준으로 구현되어 있으며, 실행 방법과 세부 구조는 [`codex/README.md`](/Users/jongwan/workspaces/private/news-crawler-remote-20260320/codex/README.md)에 정리되어 있습니다.

---

## 인증 시스템 설계 (v2)

### 개요

웹 서비스 배포를 위해 관리자/일반 사용자 역할을 구분하는 인증 시스템을 추가합니다.

### 인증 방식

- **세션 기반 (쿠키)**: Starlette `SessionMiddleware` 사용, 서명된 쿠키에 `user_id` 저장
- **비밀번호**: `bcrypt` 해싱
- **이메일 인증**: 가입 시 인증 메일 발송, 링크 클릭으로 인증 완료

### 역할

| 역할 | 설명 |
|------|------|
| `admin` | CLI 시드 커맨드로 생성. 크롤링 실행, 소스 관리, 사용자 데이터 관리 |
| `user` | 회원가입으로 생성. 기사 스크랩, 댓글, 메모 |
| 비로그인 | 기사 목록/검색/상세 열람만 가능 |

### User 테이블

```
users
───────────────
id
email (UNIQUE)
password_hash
nickname
role ("admin" | "user")
is_verified
verify_token
created_at
```

### 인증 흐름

```
회원가입: GET /auth/register → POST /auth/register → 인증 메일 발송
                                                       ↓
이메일 인증: GET /auth/verify?token=xxx → is_verified=True
                                           ↓
로그인:    GET /auth/login → POST /auth/login → 세션 저장 → 피드 리다이렉트
로그아웃:  POST /auth/logout → 세션 클리어 → 피드 리다이렉트
```

### 권한 체크

FastAPI `Depends` 함수로 구현:

- `get_current_user()` → 세션에서 user 조회, 없으면 `None` (비로그인 허용)
- `require_login()` → 미로그인 시 로그인 페이지로 리다이렉트
- `require_admin()` → 로그인 + `role=="admin"` 아니면 403

| 엔드포인트 | 권한 |
|-----------|------|
| 기사 목록/검색/상세 | 없음 (비로그인 허용) |
| 스크랩/메모/태그 | `require_login` |
| 크롤링 실행, 소스 관리 | `require_admin` |

### 메일 발송

```python
# 추상 인터페이스
class MailSender(ABC):
    def send(self, to, subject, body): ...

# SMTP 구현 (초기)
class SmtpMailSender(MailSender): ...
# → 나중에 SendGrid/SES 구현체로 교체 가능
```

### CLI 시드 커맨드

```bash
python -m cli.create_admin --email admin@example.com --password xxx --nickname 관리자
```

- `role="admin"`, `is_verified=True`로 생성 (이메일 인증 건너뜀)

### 환경변수 (.env)

```
SECRET_KEY=...              # SessionMiddleware 서명 키
BASE_URL=http://localhost:8000

# SMTP (이메일 인증)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM=...
```

### 기존 테이블 변경

- `user_notes`: `user_id` FK 추가, `(user_id, article_id)` unique constraint
- 기존 데이터는 마이그레이션 시 첫 번째 관리자에게 귀속

---

## 비교 관점

두 AI 구현체는 동일한 요구사항(스펙 문서 기반)으로 구현되었으며 다음 관점에서 비교합니다:

- **코드 구조:** 모듈 분리, 파일 설계 방식
- **테스트:** TDD 적용 방식, 테스트 커버리지
- **UI/UX:** 템플릿 구조, HTMX 활용 방식
- **API 설계:** 엔드포인트 설계, 에러 처리
- **개발 경험:** 질문/수정 횟수, 오류 수정 과정

---

## 스펙 문서

- 설계 문서: `claude/docs/superpowers/specs/2026-03-19-archive-upgrade-design.md`
- 구현 계획: `claude/docs/superpowers/plans/2026-03-19-archive-upgrade.md`
