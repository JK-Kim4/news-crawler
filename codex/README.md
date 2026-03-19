# AI Archive

FastAPI + SQLAlchemy + SQLite 기반의 개인용 AI 기술 아카이브 서비스입니다. AI 관련 기술 블로그와 피드를 수집하고, 북마크, 메모, 커스텀 태그, 전문 검색, 온디맨드 번역 기능으로 정리할 수 있습니다.

## 주요 기능

- 한국/해외 소스 분류 및 필터링
- AI 키워드 기반 기사 수집 및 점수화
- 북마크, 메모, 커스텀 태그 저장
- SQLite FTS5 기반 제목/본문 검색
- 해외 아티클 한글 요약 번역
- HTMX 기반 부분 업데이트 UI

## 요구 사항

- Python 3.11+
- SQLite FTS5 사용 가능 환경

## 설치

```bash
cd /Users/jongwan/workspaces/private/ai-news-crawler
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

개발 의존성까지 설치하려면:

```bash
python3 -m pip install -e ".[dev]"
```

Homebrew Python 환경에서는 PEP 668 때문에 시스템 Python에 직접 `pip install` 이 막힐 수 있습니다. 이 프로젝트는 가상환경 사용을 전제로 합니다.

## 실행

기본 실행:

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

브라우저에서 아래 주소로 접속:

```text
http://127.0.0.1:8000
```

## 환경 변수

- `DATABASE_URL`
  - 기본값: `sqlite:///./ai_news.db`
  - 예시:

```bash
export DATABASE_URL="sqlite:///./ai_news.db"
```

별도 설정이 없으면 프로젝트 루트에 `ai_news.db`가 생성됩니다.

## 테스트

전체 테스트 실행:

```bash
source .venv/bin/activate
pytest -q
```

## 동작 방식

앱 시작 시 아래 작업이 자동으로 수행됩니다.

- DB 테이블 초기화
- `sources` 테이블에 `country` 컬럼 마이그레이션
- `article_fts` 가상 테이블 생성 및 인덱스 재빌드
- [`config/sources.json`](/Users/jongwan/workspaces/private/ai-news-crawler/config/sources.json) 기준 소스 동기화
- 스케줄러 시작

## 주요 화면 / 엔드포인트

- `/`
  - 메인 피드
- `/bookmarks`
  - 북마크 목록
- `/search?q=rag&country=global`
  - 전문 검색
- `/sources`
  - 소스 관리
- `/articles/{id}`
  - 아티클 상세
- `POST /api/crawl`
  - 수동 크롤링 실행

## 프로젝트 구조

```text
api/             FastAPI 라우터와 템플릿 헬퍼
crawler/         소스 로딩, 크롤링, 점수화, 파이프라인
db/              SQLAlchemy 모델과 세션 초기화
config/          수집 대상 소스 설정
ui/templates/    Jinja2 + HTMX 템플릿
tests/           pytest 테스트
main.py          앱 엔트리포인트
```

## 구현 메모

- 번역은 `deep-translator`를 사용하며 DB에 저장하지 않습니다.
- 검색은 SQLite FTS5 `trigram` 토크나이저를 사용합니다.
- 커스텀 태그와 메모는 `user_notes` 테이블에 저장됩니다.
