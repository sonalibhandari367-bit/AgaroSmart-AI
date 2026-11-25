# Deploy AgroSmart-AI as one Vercel project

Import this repository **once**, with Root Directory set to the folder containing
`vercel.json`, `frontend/`, and `backend/` (normally `.`). Do not select either
subfolder as the project root.

The root configuration uses Vercel Services to build React and FastAPI together
in one deployment, with one domain and one set of project environment variables:

- `/` and frontend assets serve the React app.
- `/api/*` goes to FastAPI with the path preserved.
- `/docs`, `/redoc`, and `/openapi.json` go to FastAPI.

Vercel Services is currently in beta. Use the current Vercel CLI or dashboard
and let the root service configuration select the frameworks and build commands.
Do not override the project with a frontend-only Vite preset.

## 1. Prepare the database

The app saves recommendations and needs an external PostgreSQL database.
This is database storage, not a second Vercel app. Local SQLite remains available
for development but is rejected on Vercel because it is not persistent there.

Obtain the provider's PostgreSQL connection URI. Use `postgresql+psycopg://` as
the scheme, URL-encode special characters in credentials, and retain the
provider's required SSL parameters. Use the direct connection for migrations
and the pooled connection for deployed requests when the provider supplies both.

From `backend/`, with Python dependencies installed, set `DATABASE_URL` in your
shell or local `.env` to the direct database URI and run:

```powershell
.venv/Scripts/python.exe -m scripts.prepare_database
```

This migrates the schema and seeds the catalog. Run once before serving traffic,
and again for schema/catalog updates. Database migrations do not run on cold
starts or concurrently in preview builds.

## 2. Configure the single Vercel project

Add these variables to the project:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection URI using `postgresql+psycopg://` |
| `ADMIN_API_TOKEN` | A long random secret for administrator imports |
| `MAX_UPLOAD_BYTES` | `4000000` (leaves room for multipart overhead) |

No `VITE_API_BASE_URL` is required: Vercel builds always use `/api` on the same
domain, even if an old API URL was previously configured. Remove that old project
variable to avoid confusion. No hosted CORS configuration is needed for same-origin
requests. Existing localhost development and Docker configuration still work.

Vercel supplies `VERCEL=1`. The backend uses PostgreSQL without a per-instance
connection pool and avoids startup schema writes. Python 3.12 is selected by
`backend/.python-version`; the crop catalog is included in the API bundle.

Keep database credentials and admin tokens server-side. For preview deployments,
use a separate preview database via Vercel's environment-specific variable values.

## 3. Deploy and verify

Deploy the root project, then check the same deployment domain:

- `/` loads and shows **API connected**.
- `/api/health` reports database connected.
- `/api/crops` returns 22 crops.
- A recommendation displays five cards and expandable p5-p95 evidence.
- `/docs` loads the API documentation.

Local tests/builds verify application behavior; a cloud deployment is still needed
to verify Vercel routing and the hosted PostgreSQL connection.

References: [Vercel Services](https://vercel.com/docs/services),
[service configuration](https://vercel.com/docs/services/config-reference),
[service routing](https://vercel.com/docs/services/routing).
