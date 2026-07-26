# Job Outreach Assistant

A web application that helps job seekers discover publicly available recruitment
contact information from company websites and manage their job outreach process.

- **Backend:** Django 5.2 LTS + Django REST Framework, Celery, BeautifulSoup
- **Frontend:** React + Vite, React Router, Axios, Tailwind CSS, React Query
- **Data:** SQLite by default, PostgreSQL via a single environment variable
- **Queue:** Redis + Celery, with an inline (eager) fallback for local development

---

## Build status

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Backend foundation — structure, settings, user model, common layer, DRF/JWT/OpenAPI | ✅ Complete |
| 2 | Authentication — register, login, refresh, logout, change password, profile | ✅ Complete |
| 3 | Companies + Notes | ✅ Complete |
| 4 | Crawler, email extraction, classification, Contacts | ✅ Complete |
| 5 | Applications tracker + Dashboard | ✅ Complete — **backend done** |
| 6 | Frontend foundation — Vite, Tailwind, router, axios, React Query, auth | ✅ Complete |
| 7 | Frontend feature pages | ✅ Complete |
| 8 | Tests, documentation, polish | ⏳ Pending |

---

## Containers and Kubernetes

Two independently built images:

| Image | Context | Contents |
|---|---|---|
| `haze21/joa-backend` | `./backend` | Python 3.12, gunicorn, non-root, static collected at build |
| `haze21/joa-frontend` | `./frontend` | Vite build served by nginx with SPA fallback |

```bash
docker build -t haze21/joa-backend:latest ./backend
```

```bash
docker build -t haze21/joa-frontend:latest ./frontend
```

The backend image serves **both** the web process and the Celery worker — same
image, different command. A worker running a different build of the task code
than the process that enqueued the job is a genuinely nasty bug class.

CI builds each image only when its own directory changes
(`.github/workflows/backend-image.yml`, `frontend-image.yml`).

**k3s manifests are in [`deploy/k3s/`](deploy/k3s/) — see
[its README](deploy/k3s/README.md) for the deploy sequence and the gotchas.**

The one structural change when Celery runs in its own pod: **SQLite stops being
viable.** Two pods cannot safely share a SQLite file, so Postgres becomes
mandatory. No application code changes — it already reads `DATABASE_URL`.

---

## Requirements

- Python 3.12+
- Node.js 20+ (from Phase 6)
- Optional: Docker (for PostgreSQL + Redis), or a local Redis install

---

## Backend setup

```bash
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements/development.txt
cp .env.example .env
```

Generate a secret key and paste it into `.env` as `DJANGO_SECRET_KEY`:

```bash
.venv/Scripts/python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Apply migrations and start the server:

```bash
.venv/Scripts/python.exe manage.py migrate
```

```bash
.venv/Scripts/python.exe manage.py runserver
```

The API is then available at <http://127.0.0.1:8000/api/>.

### Useful endpoints

| URL | Purpose |
|-----|---------|
| `/api/health/` | Liveness probe (public) |
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | Raw OpenAPI 3 schema |
| `/admin/` | Django admin |

### Authentication API

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register/` | — | Create an account; returns a JWT pair |
| POST | `/api/auth/login/` | — | Exchange email + password for a JWT pair |
| POST | `/api/auth/refresh/` | — | Rotate the refresh token, get a new access token |
| POST | `/api/auth/logout/` | Bearer | Blacklist a refresh token, ending that session |
| POST | `/api/auth/change-password/` | Bearer | Change password, revoke other sessions |
| GET/PUT/PATCH | `/api/auth/profile/` | Bearer | Read and update your own profile |

Notes on behaviour:

- **Email is the login identifier** and is matched case-insensitively.
- **Refresh tokens rotate.** Each refresh blacklists the token you submitted and
  returns a new one, so a stolen refresh token is usable at most once. Clients
  must store the new value.
- **Changing your password revokes every other session** and returns a fresh
  pair for the device that made the change.
- **Login failures are indistinguishable.** A wrong password and an unknown
  email return byte-identical responses, so the API cannot be used to
  enumerate registered addresses.
- **Email is read-only on the profile.** It is the login identifier, and the
  MVP has no email-delivery capability to verify a change.

### Companies API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/companies/` | List, search, filter, sort, paginate |
| POST | `/api/companies/` | Add a company |
| GET | `/api/companies/{id}/` | Company detail |
| PUT / PATCH | `/api/companies/{id}/` | Replace / update |
| DELETE | `/api/companies/{id}/` | Delete (cascades to notes) |

Query parameters on the list endpoint:

| Parameter | Behaviour |
|---|---|
| `search` | Partial, case-insensitive across name, industry, country |
| `industry` | Exact, case-insensitive |
| `country` | Exact, case-insensitive |
| `ordering` | `name`, `created_at`, `updated_at`, `industry`, `country`; prefix `-` to reverse |
| `page`, `page_size` | Pagination (page size capped at 100) |

### Notes API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/notes/?company={id}` | List notes, optionally for one company |
| POST | `/api/notes/` | Add a note to one of your companies |
| GET/PUT/PATCH/DELETE | `/api/notes/{id}/` | Read / update / delete a note |

Notes on behaviour:

- **Website URLs are normalised on write.** `Example.com/` and
  `https://EXAMPLE.com` both store as `https://example.com`. Embedded
  credentials, default ports, trailing slashes, and fragments are stripped.
- **Company names are unique per user, case-insensitively.** Two different job
  seekers may both track "Acme Ltd"; one user cannot add it twice. Enforced by
  a database constraint, not just serializer validation.
- **`PUT` truly replaces.** Optional fields omitted from a `PUT` are reset to
  empty. `PATCH` leaves omitted fields untouched.
- **Two kinds of notes, by design.** `Company.notes` is a free-text scratchpad
  on the company record; `Note` rows are individual timestamped log entries.
  The specification lists both, and they are independent.

### Scanner API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/scan/{company_id}` | Start a scan; returns `202` with a pending scan |
| GET | `/api/scan/status/{scan_id}` | Live progress plus every page visited |

Both accept an optional trailing slash.

### Contacts API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/contacts/` | List, search, filter, sort, paginate |
| GET | `/api/contacts/{id}/` | Contact detail |
| PATCH | `/api/contacts/{id}/` | Set `notes` and `is_favourite` |

Query parameters: `search` (email, notes, company name), `company`,
`classification`, `is_favourite`, `recruitment_only`, `ordering`.

Contacts cannot be created or deleted through the API — they exist because a
scan found them on a public page. `email`, `classification`, and provenance
fields are read-only.

### Applications API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/applications/` | List, search, filter, sort, paginate |
| POST | `/api/applications/` | Record an application |
| GET | `/api/applications/{id}/` | Application detail |
| PUT / PATCH | `/api/applications/{id}/` | Replace / update |
| DELETE | `/api/applications/{id}/` | Delete |

Statuses form a lifecycle: `draft` → `sent` → `waiting` → `interview` →
`offer` / `rejected` → `closed`.

Query parameters: `search` (position, company name, contact email, notes),
`status`, `company`, `is_sent`, `is_pending`, `applied_after`,
`applied_before`, `ordering`.

Validation, per the specification: **company, position and status are all
required**. `status` has no serializer default, so an incomplete payload is
rejected rather than silently becoming a draft.

### Dashboard API

`GET /api/dashboard/` returns every widget counter for the current user:

```json
{
  "total_companies": 2,
  "companies_scanned": 1,
  "total_contacts": 8,
  "favourite_contacts": 0,
  "total_applications": 8,
  "applications_sent": 8,
  "pending_applications": 3,
  "interviews": 1,
  "offers": 1,
  "rejections": 2,
  "drafts": 0,
  "applications_by_status": {
    "draft": 0, "sent": 2, "waiting": 1, "interview": 1,
    "offer": 1, "rejected": 2, "closed": 1
  }
}
```

Definitions worth knowing:

- **`applications_sent`** counts everything past draft — an application at
  interview stage was still sent. `applications_by_status` is included so the
  frontend never has to re-derive this.
- **`pending_applications`** means sent or waiting: no outcome recorded yet.
- **`companies_scanned`** counts companies with at least one *completed* scan;
  a failed scan does not count, and several completed scans still count once.

The whole payload is three database queries regardless of how much data the
user has — there is a test asserting the count does not grow with row count.

### Recovering a scan after a page reload

`GET /api/companies/{id}/` includes a `last_scan` object (or `null`):

```json
"last_scan": {
  "id": "…", "status": "running", "progress_percent": 40,
  "is_active": true, "pages_scanned": 4, "pages_discovered": 10,
  "contacts_found": 2, "started_at": "…", "finished_at": null,
  "error_message": "", "created_at": "…"
}
```

This is how the scan-progress screen recovers its `scan_id` after a reload —
otherwise the id only ever appears in the response to the POST that started the
scan. It is deliberately **not** on the companies *list* endpoint, which would
cost one query per row for a value that list does not display.

---

## How scanning works

A scan validates the company's website, records a `pending` scan, and queues
the crawl. Poll `/api/scan/status/{scan_id}` while `is_active` is true.

**The crawler is deliberately polite and deliberately limited:**

| Guard | Behaviour |
|---|---|
| robots.txt | Fetched once per host and obeyed; disallowed paths are never requested |
| Rate limit | At least `CRAWLER_DELAY_SECONDS` between requests (default 0.5s) |
| Page budget | Stops after `CRAWLER_MAX_PAGES` (default 40) |
| Depth | Stops after `CRAWLER_MAX_DEPTH` links from the homepage (default 2) |
| Identity | Honest `User-Agent` naming the tool and its purpose |
| Scope | Same site only — subdomains yes, social networks and third parties no |
| Response size | Capped at `CRAWLER_MAX_RESPONSE_BYTES`; only HTML is read |

**SSRF protection.** The crawler follows user-supplied URLs, so every request is
checked before it is made: `http`/`https` only, and the hostname must resolve
*exclusively* to public addresses. Loopback, private ranges, link-local
(including the `169.254.169.254` cloud-metadata endpoint), multicast, and
reserved ranges are all refused. Redirects are followed manually so each hop is
re-validated — a public URL that redirects to an internal one is caught.

`CRAWLER_ALLOW_PRIVATE_NETWORKS` disables these checks. It exists so the test
suite can crawl a local fixture server. **It must stay `False` anywhere real
users can reach the API.**

**Three discovery sources, in order.** Following `<a href>` links is not enough
on its own: plenty of modern sites navigate with JavaScript — a React header
renders `<button>Careers</button>` with a click handler and no anchor — leaving
a public, indexed careers page unreachable to any link-following crawler.

1. **Links** in the fetched HTML.
2. **`sitemap.xml`**, located via robots.txt's `Sitemap:` directive or the usual
   paths. It lists a site's public URLs regardless of how navigation is built.
3. **Well-known path probing** for any page type the first two missed —
   `/careers`, `/jobs`, `/contact`, `/join-us` and friends. Only for missing
   types, so a normally-linked site costs no extra requests. Probes that 404 are
   not recorded as pages and do not consume the page budget.

Pages are prioritised rather than spidered exhaustively: careers and jobs
pages first, then contact, team, leadership, about, and press. The budget is
spent where recruitment contacts actually live.

**Obfuscated addresses are decoded.** Two schemes are handled beyond plain text
and `mailto:` links:

- **Cloudflare Email Address Obfuscation**, which is on by default for a great
  many sites. It replaces the address with the literal text
  `[email protected]` and hides the real value XOR-encoded in a `data-cfemail`
  attribute. Undecoded, those pages look like they contain no addresses at all.
- **Hand-written anti-scraping text** such as `careers [at] example [dot] com`,
  including `(at)`, `{at}` and `-at-` forms.

A bare `at` is deliberately *not* treated as `@` — "contact us at example.com"
is ordinary English, and reading it as an address would invent
`us@example.com`. Precision is worth more than recall here, because a false
positive is a junk contact the user has to notice and clean up.

Extracted addresses are classified from the local part of the address —
`careers@` → Careers, `recruitment@` → Recruitment, `support@` → Support, and
so on, falling back to `unknown`. Duplicates are stored once per company.

> **Eager mode caveat.** With `CELERY_TASK_ALWAYS_EAGER=True` the crawl runs
> inline, so `POST /api/scan/{id}` blocks until the scan finishes — with the
> default 1-second delay and a 25-page budget that can be ~25 seconds. For
> genuinely backgrounded scans, set it to `False` and run a worker.

Create an admin account with:

```bash
.venv/Scripts/python.exe manage.py createsuperuser
```

---

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env.local
```

```bash
npm run dev
```

The app runs at <http://localhost:5173>. Start the backend too — the Vite dev
server proxies `/api` to `http://127.0.0.1:8000`, so the browser only ever
talks to one origin and there are no CORS preflights in development.

| Command | Purpose |
|---|---|
| `npm run dev` | Dev server with hot reload |
| `npm run build` | Production bundle into `dist/` |
| `npm run preview` | Serve the built bundle locally |
| `npm run lint` | Lint with oxlint |

### Pages

| Route | Purpose |
|---|---|
| `/login`, `/register` | Public |
| `/dashboard` | Widget counters and a status breakdown |
| `/companies` | List with search, industry/country filters, sorting, pagination |
| `/companies/new` | Add a company |
| `/companies/:id` | Detail: scan panel, notes, contacts, edit and delete |
| `/scans/:scanId` | Live scan progress and the pages visited |
| `/contacts` | Search, classification/company filters, favourites, notes, copy email |
| `/applications` | Full CRUD with status tracking |
| `/notes` | All notes, filterable by company |
| `/profile` | Name and email |
| `/settings` | Password and account |

> The specification lists Profile and Settings separately without saying what
> belongs on each. The split used: **Profile** is who you are (name, email),
> **Settings** is account security (password, sign out).

### How the frontend is put together

| Concern | Where | Note |
|---|---|---|
| Session state | `src/store/AuthProvider.jsx` | Routing depends on it synchronously; a route guard cannot await a query |
| Server state | React Query hooks in `src/hooks/` | Everything fetched from the API |
| API access | `src/services/apiClient.js` | One Axios instance; nothing else talks to the network |
| Token storage | `src/store/tokenStorage.js` | Single module, so the strategy is swappable |
| Error reading | `src/utils/errors.js` | The one place that understands the API's error envelope |

**Token refresh is single-flight.** When several queries hit an expired access
token at once they all receive 401s, but only one `/auth/refresh/` call is made
and the rest wait for it. Without that, parallel refreshes race and all but one
present a token that rotation has already blacklisted — signing the user out
for no reason.

**Tokens live in `localStorage`.** The trade-off is stated plainly in
`tokenStorage.js`: it survives a reload, but any XSS bug could read it. The
safer option — httpOnly cookies — needs the backend to move from `Authorization:
Bearer` to cookie auth with CSRF protection. Short access-token lifetimes and
refresh rotation limit the damage as built.

---

## Configuration

All configuration is environment-driven — see `backend/.env.example` for the full
list. The two switches that matter most:

**Database.** `DATABASE_URL` selects the backend. SQLite is the default; moving to
PostgreSQL requires no code change:

```
DATABASE_URL=postgres://joa:joa@127.0.0.1:5432/job_outreach
```

**Background processing.** `CELERY_TASK_ALWAYS_EAGER=True` runs website scans
inline in the web process, so the application is fully usable with no broker.
Set it to `False` and run a worker for true background processing:

```bash
docker compose up -d
```

```bash
cd backend && .venv/Scripts/celery.exe -A config worker -l info --pool=solo
```

> `--pool=solo` is required on Windows; on Linux/macOS omit it.

---

## Settings layout

| Module | Used for |
|--------|----------|
| `config.settings.base` | Everything shared; reads all env vars |
| `config.settings.development` | `DEBUG=True`, browsable API, console email |
| `config.settings.production` | Fails fast on missing secrets, HSTS/SSL, WhiteNoise |
| `config.settings.test` | In-memory SQLite, fast hasher, eager Celery |

`manage.py` defaults to `config.settings.development`; deployments must set
`DJANGO_SETTINGS_MODULE` explicitly.

---

## Testing

```bash
cd backend && .venv/Scripts/python.exe -m pytest
```

With coverage:

```bash
cd backend && .venv/Scripts/python.exe -m pytest --cov --cov-report=term-missing
```

Lint:

```bash
cd backend && .venv/Scripts/python.exe -m ruff check .
```

Django's own checks (including the production-hardening set):

```bash
cd backend && .venv/Scripts/python.exe manage.py check --deploy --settings=config.settings.production
```

---

## API conventions

**Errors.** Every failure uses one envelope, so the frontend needs a single
error branch:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input.",
    "details": { "website": ["Enter a valid URL."] }
  }
}
```

**Pagination.** Every list endpoint is paginated and accepts `?page=` and
`?page_size=` (capped at 100):

```json
{
  "count": 42,
  "total_pages": 3,
  "page": 1,
  "page_size": 20,
  "next": "http://.../api/companies/?page=2",
  "previous": null,
  "results": []
}
```

**Authentication.** JWT bearer tokens (`Authorization: Bearer <access>`).
Refresh tokens rotate and old ones are blacklisted, so logout genuinely ends a
session.

**Rate limiting.** The auth endpoints are throttled per scope; all other
endpoints are unaffected. Limits are configurable — see `THROTTLE_AUTH_*` in
`.env.example`. A throttled request returns `429` in the standard envelope.

**Ownership.** Every domain record belongs to one user. Querysets are filtered
by owner, so another user's record returns `404`, never `403` — the API never
confirms that a given id exists for someone else.
