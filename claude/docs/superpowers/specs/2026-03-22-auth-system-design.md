# Auth System Design

Session-based authentication with admin/user roles for web deployment.

## Requirements

- Session-based auth (Starlette SessionMiddleware, signed cookies)
- Email + password registration with email verification
- Admin created via CLI seed command
- Non-authenticated users can browse articles; login required for scrap/comments; admin required for crawling/source management
- SMTP mail sender initially, abstracted for future replacement
- CSRF protection on all state-changing endpoints
- Password reset flow

## Data Model

### User table

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| email | String, UNIQUE | Login identifier |
| password_hash | String | bcrypt hash (via `passlib[bcrypt]`) |
| nickname | String | Display name |
| role | String | "admin" or "user" (default: "user") |
| is_verified | Boolean | Email verification status (default: False) |
| verify_token | String, nullable | UUID token, null after verification |
| verify_token_expires_at | DateTime, nullable | Token expiry (UTC, 24h from creation) |
| reset_token | String, nullable | Password reset UUID token |
| reset_token_expires_at | DateTime, nullable | Reset token expiry (UTC, 1h from creation) |
| created_at | DateTime | UTC |

### Existing table changes

**`user_notes` migration strategy (SQLite-specific):**

1. `init_db()` adds `user_id` column: `ALTER TABLE user_notes ADD COLUMN user_id INTEGER REFERENCES users(id)` (nullable initially, wrapped in try/except for idempotency)
2. After admin seed, a startup step sets `user_id` to the first admin's ID for all rows where `user_id IS NULL`
3. The old `UNIQUE(article_id)` constraint remains at DB level (SQLite cannot drop constraints). Uniqueness of `(user_id, article_id)` is enforced at application level via a check before insert.

## Session

- `SessionMiddleware` with `SECRET_KEY` from env
- `max_age=604800` (7 days), `https_only=True` in production
- Session stores `user_id` only
- No server-side session table

## CSRF Protection

- Use `starlette-csrf` middleware (CsrfProtect)
- Validates `Origin`/`Referer` headers on all POST requests
- HTMX requests include CSRF token via `hx-headers` attribute set globally on `<body>`
- Token exposed to templates via `request.state.csrf_token`

## Auth Endpoints

### Registration

1. `GET /auth/register` — registration form (email, nickname, password, password confirmation)
2. `POST /auth/register` — validate, create User (`is_verified=False`), send verification email, redirect to verify-pending page
   - If email already exists and is verified: show "이미 가입된 이메일입니다" error
   - If email exists but not verified: regenerate token, resend verification email, show verify-pending page
3. `GET /auth/verify?token=xxx` — verify token + check expiry, set `is_verified=True`, clear token fields, redirect to login
   - Expired token: show error with "인증 메일 재발송" link

### Login / Logout

1. `GET /auth/login` — login form
2. `POST /auth/login` — verify email/password, check `is_verified`, store `user_id` in session, redirect to feed
3. `POST /auth/logout` — clear session, redirect to feed

### Password Reset

1. `GET /auth/forgot-password` — email input form
2. `POST /auth/forgot-password` — generate `reset_token` (1h expiry), send reset email. Always show "메일을 확인해주세요" (even if email not found, to prevent enumeration)
3. `GET /auth/reset-password?token=xxx` — new password form
4. `POST /auth/reset-password` — validate token + expiry, update password_hash, clear token, redirect to login

### Resend Verification

1. `POST /auth/resend-verification` — accepts email, generates new token (24h), sends new email

## Permission Dependencies

Three FastAPI `Depends` functions in `auth/dependencies.py`:

- `get_current_user(request, db)` — returns User or None from session
- `require_login(request, db)` — if not authenticated:
  - Full-page request: HTTP 302 redirect to `/auth/login`
  - HTMX request (detected via `HX-Request` header): return 401 with `HX-Redirect: /auth/login` header
- `require_admin(request, db)` — if not admin:
  - Full-page request: HTTP 403
  - HTMX request: return 403 with error HTML fragment

### Endpoint permissions

| Endpoint | Permission |
|----------|-----------|
| Feed, search, article detail | None (public) |
| Bookmark, memo, tags | `require_login` |
| Crawl trigger, source management | `require_admin` |

## User Context Injection

- Middleware sets `request.state.user` on every request by reading session `user_id`
- Templates access current user via `request.state.user` (no need to pass through every context dict)
- `build_sidebar_context(db, user)` accepts optional user to scope bookmark count
- `get_or_create_user_note(db, article, user_id)` updated to accept `user_id`
- `enrich_article(article, user_id)` / `enrich_articles(articles, user_id)` scoped to current user's notes

## Mail Sending

### Abstraction

```python
# auth/mail.py
class MailSender(ABC):
    def send(self, to: str, subject: str, body: str) -> None: ...

class SmtpMailSender(MailSender):
    # Uses SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
    ...
```

### Email templates

- Verification: "AI Archive 이메일 인증" — "{BASE_URL}/auth/verify?token={uuid}"
- Password reset: "AI Archive 비밀번호 재설정" — "{BASE_URL}/auth/reset-password?token={uuid}"

## CLI Seed Command

```bash
python -m cli.create_admin --email admin@example.com --password xxx --nickname 관리자
```

- Creates user with `role="admin"`, `is_verified=True`
- Fails with error if email already exists

## Environment Variables (.env)

```
SECRET_KEY=...
BASE_URL=http://localhost:8000
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM=...
```

## File Structure

New files:

```
claude/
├── auth/
│   ├── dependencies.py    # get_current_user, require_login, require_admin
│   ├── router.py          # /auth/* endpoints
│   ├── middleware.py       # UserContextMiddleware (sets request.state.user)
│   ├── mail.py            # MailSender ABC + SmtpMailSender
│   └── password.py        # passlib[bcrypt] hash/verify
├── cli/
│   └── create_admin.py    # python -m cli.create_admin
└── ui/templates/auth/
    ├── login.html
    ├── register.html
    ├── verify_pending.html
    ├── forgot_password.html
    └── reset_password.html
```

Modified files:

- `main.py` — add SessionMiddleware, CSRF middleware, UserContextMiddleware, auth router
- `db/models.py` — add User model
- `db/session.py` — include users table in init_db(), user_notes migration
- `api/articles.py` — add require_login to scrap/memo/tags, pass user_id to helpers
- `api/sources.py` — add require_admin to source management
- `api/helpers.py` — update get_or_create_user_note, build_sidebar_context, enrich functions to accept user_id
- `base.html` — conditional menu rendering by role, login/logout UI, CSRF token in hx-headers
- `pyproject.toml` — add passlib[bcrypt], starlette-csrf, python-dotenv

## UI Changes

### Sidebar menu visibility

| Menu | Non-auth | User | Admin |
|------|----------|------|-------|
| Feed | O | O | O |
| Search | O | O | O |
| Bookmarks | X | O | O |
| Source management | X | X | O |
| Crawl button | X | X | O |
| Footer | Login/Register links | Nickname/Logout | Nickname/Logout |

### Article card actions

- Bookmark/memo/tags: login required (hidden for non-auth)
- Read toggle/external link: visible to all

### Auth pages

- Inherit base.html layout (with sidebar)
- Centered form card in main content area (Tailwind)
- Login: email + password + submit + "회원가입" link + "비밀번호 찾기" link
- Register: email + nickname + password + password confirm + submit + "로그인" link
- Verify pending: "인증 메일을 발송했습니다. 이메일을 확인해주세요."
- Forgot password: email input + submit
- Reset password: new password + confirm + submit

## Known Limitations

- `is_read` on `Article` model remains global (not per-user). Consider moving to `UserNote` in future iteration.
- Rate limiting on auth endpoints deferred to follow-up (consider `slowapi`).
- Session invalidation is client-side only (cookie deletion). No server-side session revocation.
