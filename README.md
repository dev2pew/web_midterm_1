# LUCKYFORUMS

A minimal, backend-first discussion forum built with Django and Django REST Framework. It targets a classic ~2010 web layout (header + sidebar + content), keeps the visual theme intentionally blank, and focuses on clean APIs, tests, and basic security.

## OVERVIEW

`LuckyForums` provides...

- Accounts: register, login/logout (session UI) and JWT API auth for programmatic access
- Forum: threads and posts with ratings (+1/-1), edit history (admin-visible), and deletions that cascade history
- Profiles: editable profiles (avatar, bio, device), profile comments with ratings and edit history
- Roles & moderation: user/admin roles; admins can override permissions, silence or ban users
- Notifications: thread replies, profile comments, and @mentions
- Timestamps: all API timestamps are UNIX seconds; browser computes badges and formatted dates
- Tests and tooling: `pytest` test suite, `Black` + `isort` formatting

## STACK

- Language: `Python` 3.11.14
- Frameworks: `Django` 4.2.x, Django `REST` Framework (`DRF`)
- Auth: `Django` session auth for UI, `SimpleJWT` for API tokens
- DB: `PostgreSQL` (docker-compose service)
- Front-end: `Django` templates + `Bootstrap` 5 + `jQuery` (`AJAX`)
- Tooling: `Poetry`, `Black`, `isort`, `pytest`, `pytest-django`

## LIBRARIES

- `django`, `djangorestframework`, `djangorestframework-simplejwt`
- `drf-nested-routers`, `django-filter`
- `pillow` (avatars), `python-decouple` (env), `shortuuid`, `bleach`/`markdown` (optional content safety)
- Dev: `black`, `isort`, `flake8`, `pytest`, `pytest-django`, `pytest-cov`, `model-bakery`

## PROJECT STRUCTURE

```plain
.
├── lucky_forums/            # PROJECT SETTINGS, URLS
├── forum/                   # THREADS, POSTS, RATINGS, PAGES AND API
│   ├── models.py            # THREAD, POST, POSTEDIT, POSTRATING
│   ├── serializers.py       # THREADSERIALIZER, POSTSERIALIZER (+UNIX TIMESTAMPS)
│   ├── views.py             # VIEWSETS: THREAD, POST; RATING/HISTORY ACTIONS
│   ├── api_urls.py          # /API/THREADS/, NESTED POSTS
│   ├── pages.py             # HOME (LIST), THREAD DETAIL/EDIT PAGES
│   ├── templates/           # BASE LAYOUT, FORUM PAGES
│   └── static/forum/app.js  # AJAX LOGIC (THREADS/POSTS, BADGES, NOTIFICATIONS)
├── users/                   # AUTH, PROFILES, COMMENTS/RATINGS, MODERATION, NOTIFICATIONS
│   ├── models.py            # PROFILE(+SILENCED/BANNED), PROFILECOMMENT, PROFILECOMMENTEDIT, NOTIFICATION
│   ├── serializers.py       # USER/PROFILE/PROFILECOMMENT (+UNIX TIMESTAMPS)
│   ├── api_urls.py          # /API/AUTH/; PROFILE APIS UNDER /API/USERS/
│   ├── profile_views.py     # PROFILE API VIEWS
│   ├── notifications.py     # NOTIFY THREAD REPLIES / PROFILE COMMENTS / MENTIONS
│   ├── notifications_api.py # LIST AND MARK READ
│   ├── moderation_api.py    # ADMIN SILENCE/BAN
│   ├── notifications_api_urls.py
│   ├── moderation_api_urls.py
│   ├── pages.py             # SESSION REGISTER PAGE + PROFILE SHELLS
│   └── templates/           # REGISTRATION/LOGIN, USERS/PROFILE PAGES
├── scripts/                 # FORMAT.SH, RESET.SH
├── docker-compose.yml       # POSTGRESQL (16-ALPINE)
├── Dockerfile               # MULTI-STAGE POETRY BUILD
├── pyproject.toml           # POETRY + DEV TOOLING CONFIG
└── README.md
```

## FEATURES

- Registration & Login
  - Session-based UI (CSRF-protected) and JWT endpoints for API clients
  - Profiles auto-created upon registration (backfilled for existing users)

- Forum
  - threads (create, list, retrieve, edit, delete)
  - Posts within threads (create, list, edit, delete) with +1/-1 ratings
  - Edit history stored and returned only to admins; deleted content removes its history

- Profiles
  - Editable (avatar, bio, device) with placeholder avatar if none
  - Profile comments (create, list, edit, delete) with ratings and admin-visible edits history

- Roles and Moderation
  - Users own their content; admins can override permissions
  - Profile owners can moderate comments on their own profile
  - Admins can silence or ban users via API

- Notifications
  - Thread reply, profile comment, and @mention events
  - Simple list & mark-read API

- Timestamps & Badges
  - All API timestamps are UNIX seconds
  - Browser computes: newbie (< 7 days), and dynamic “N years” badges; role/state badges (user/admin/silenced/banned)

## GETTING STARTED

Prereqs...

- `Python` 3.11.14
- `Poetry`
- `Docker` + `Docker Compose`

1) Install dependencies

```bash
poetry env use 3.11.14
poetry install --no-root
```

2) Start `PostgreSQL`

```bash
docker compose up -d postgres
```

3) Environment file (.env)

```bash
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
SECRET_KEY=replace-me
POSTGRES_DB=file_forum
POSTGRES_USER=file_forum_user
POSTGRES_PASSWORD=file_forum_pass
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

4) Migrate and (optionally) create admin

```bash
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
```

5) Run dev server

```bash
poetry run python manage.py runserver 0.0.0.0:8000
```

## API SURFACE (ESSENTIALS)

Auth (JWT)...

- POST /api/auth/register/ {username, email?, password, password2}
- POST /api/auth/token/ {username, password}
- POST /api/auth/token/refresh/ {refresh}
- GET  /api/auth/me/

Forum...

- GET  /api/threads/
- POST /api/threads/ {title}
- GET  /api/threads/{slug}/
- PATCH/DELETE /api/threads/{slug}/ (owner/admin)
- GET  /api/threads/{slug}/posts/
- POST /api/threads/{slug}/posts/ {body}
- PATCH/DELETE /api/threads/{slug}/posts/{id}/ (owner/admin)
- POST/DELETE /api/threads/{slug}/posts/{id}/rate/ {value: 1|-1}
- GET  /api/threads/{slug}/posts/{id}/history/ (admin)

Profiles & comments...

- GET  /api/users/{username}/profile/
- GET/PATCH /api/users/me/profile/
- GET/POST /api/users/{username}/comments/
- PATCH/DELETE /api/users/{username}/comments/{id}/ (author/admin or profile owner)
- POST/DELETE /api/users/{username}/comments/{id}/rate/
- GET  /api/users/{username}/comments/{id}/history/ (admin)

Moderation & notifications...

- PATCH /api/users/{username}/moderation/ {silenced_until?, banned_until?} (UNIX; admin)
- GET   /api/notifications/?unread=1
- POST  /api/notifications/{id}/read/

Notes...

- All datetime fields are UNIX seconds; clients format them as needed.
- Badges are computed on the client from user metadata (role, join date, moderation state).

## FRONT-END

- Classic ~2010 layout (header + left sidebar + content)
- Bootstrap 5 + jQuery; AJAX-driven for thread and profile flows
- Blank theme; minimal styling; avatars shown everywhere with placeholders

## MODERATION

- Silence/Ban stored on Profile with UNIX timestamps
- Silenced/Banned users cannot create/edit posts, threads, or profile comments
- Admins can delete or edit content and view histories

## TESTS & STANDARDS

- Tests: pytest suite (API, pages, permissions, notifications, moderation, formatting)

```bash
poetry run pytest -q
```

- Formatting & imports...

```bash
bash scripts/format.sh        # FORMAT
bash scripts/format.sh check  # CHECK-ONLY
```

- Standards...

  - API timestamps are UNIX seconds
  - Browsers compute small date/math (badges, relative times)
  - Basic security: CSRF for session, JWT for API, role/ownership checks, admin overrides

## SCRIPTS

- scripts/reset.sh: resets DB in the running Postgres container, deletes migrations, re-creates/migrates
- scripts/format.sh: runs isort and black (format or check mode)

## DOCKER

- docker-compose.yml provides a Postgres 16 service on ${POSTGRES_PORT:-5432}
- Dockerfile builds a slim Python 3.11 image with Poetry-installed deps

## ROADMAP (FUTURE IDEAS)

- Background workers for digest notifications
- Richer moderation audit trails
- Optional markdown preview and safe rendering
- Pagination and search
