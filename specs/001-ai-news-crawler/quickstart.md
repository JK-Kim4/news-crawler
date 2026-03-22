# Quickstart: AI News Crawler

**Date**: 2026-03-23 | **Branch**: `001-ai-news-crawler`

## Prerequisites

- Python 3.11+
- pip (또는 uv)

## Setup

```bash
cd spec-kit/

# 가상환경 생성 + 활성화
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -e ".[dev]"

# 환경변수 설정
cp .env.example .env
# .env 파일에서 SECRET_KEY 설정

# 서버 실행 (DB 자동 초기화)
uvicorn main:app --reload --port 8000
```

## Initial Admin Account

```bash
python scripts/seed_admin.py
# admin@example.com / admin123
```

## Key URLs

| URL | Description |
|-----|-------------|
| http://localhost:8000 | 메인 피드 (게시물 목록) |
| http://localhost:8000/auth/login | 로그인 |
| http://localhost:8000/auth/register | 회원가입 |
| http://localhost:8000/search | 검색 |
| http://localhost:8000/my/scraps | 내 스크랩 |
| http://localhost:8000/admin/sources | 관리자: 소스 관리 |
| http://localhost:8000/admin/users | 관리자: 사용자 관리 |
| http://localhost:8000/admin/scoring-weights | 관리자: 가중치 관리 |
| http://localhost:8000/admin/crawl-failures | 관리자: 크롤링 알림 |

## Development

```bash
# 서버 실행
uvicorn main:app --reload --port 8000

# 테스트 실행
pytest tests/

# 수동 크롤링 (관리자 로그인 후 사이드바 '크롤링' 버튼 클릭)
```
