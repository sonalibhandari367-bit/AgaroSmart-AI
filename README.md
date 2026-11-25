# AgroSmart AI

Responsive crop comparison app with a React/TypeScript/Vite frontend, FastAPI/Pydantic API, Pandas CSV validation, SQLAlchemy persistence, PostgreSQL, Alembic migrations, and Docker Compose.

## Data provenance and recommendation behavior

The included crop observations were converted from the user-provided `Crop_recommendation.xlsx`: 2,200 rows, 22 crop labels, seven numeric inputs, no missing or duplicate rows in the source file. The workbook gives no independently verified source citation and documents no measurement units. Its values and derived minimum/maximum/mean ranges are therefore labeled **user-provided and unverified**; entered values must use the same conventions as the dataset. No independent agronomic requirement has been added. Optional soil type, location, and season are recorded but are not modeled. The ranking algorithm uses standardized distance from crop means and an exponential similarity score; evidence uses the p5–p95 range; it is not a validated yield model, probability, or planting recommendation.

## Local setup (Docker; recommended)

Requirements: Docker Desktop with Compose v2. Copy `.env.example` to `.env`, replace both values with local random values, then run from the repository root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Compose starts PostgreSQL 16, runs Alembic migrations before FastAPI, then serves the frontend at `http://localhost:5173` and API docs at `http://localhost:8000/docs`. Health check: `http://localhost:8000/api/health`. Compose refuses to start until both placeholder values have been replaced. Keep the services bound to localhost for local development.

To stop services, run `docker compose down`. To also remove local database data, run `docker compose down -v` (destructive to the local database).

## Local setup without Docker

Use Python 3.11+, Node 20+, and a reachable PostgreSQL 14+ database. Create backend and frontend environments from their examples. Set `DATABASE_URL`, `ADMIN_API_TOKEN`, `CORS_ORIGINS` in `backend/.env`; use `VITE_API_BASE_URL=http://localhost:8000/api` in `frontend/.env.local`.

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

For a lightweight API-only smoke run without PostgreSQL, set `DATABASE_URL=sqlite:///./agrosmart.db` before launching. Production and Compose use PostgreSQL.

## Tests and builds

```powershell
cd backend
pip install -e ".[dev]"
pytest
```

```powershell
cd frontend
npm install
npm test
npm run build
```

The backend API tests use a local SQLite database unless `DATABASE_URL` is already set. Run them in an isolated shell/environment. There are no claims of tests passing until the commands are executed.

## API / administration

See [docs/API.md](docs/API.md). CSV uploads need the server-side `ADMIN_API_TOKEN` header `X-Admin-Token`; do not put the token in the browser bundle. Current imports generate a cleaned quality report and dataset version metadata but deliberately do not replace the catalog. Create and review a trusted dataset before activating new crop ranges.

## Vercel deployment

Deploy the entire app as one Vercel project from the repository root. The root `vercel.json` serves the frontend and `/api` on the same domain. Follow [the Vercel deployment guide](docs/VERCEL.md) for database setup and deployment checks.

## Security and operations

No credentials are committed. Admin imports are protected by constant-time token comparison, CSV allow-list/extension check, byte limit, schema validation and bounded numeric ranges. CORS is explicit and credentialless. SQL writes use SQLAlchemy parameters. The token auth is a single-admin deployment control, not user identity management; rotate it through the host environment. Configure production HTTPS, backups, monitoring and stronger identity integration before multi-user public operation.

## Troubleshooting

- Docker not found: install/start Docker Desktop Compose, or use the manual PostgreSQL/Python/Node setup.
- API database unavailable: check `DATABASE_URL`, PostgreSQL readiness and credentials; run `cd backend; alembic upgrade head`.
- Browser reports network/CORS errors: verify the API is listening and exact frontend origin is listed in backend `CORS_ORIGINS`.
- No candidates: check API response; validated in-range data returns up to 22 candidates, sorted by similarity.
- Import rejected: CSV must contain `nitrogen,phosphorus,potassium,temperature_c,humidity_pct,ph,rainfall_mm,crop` columns (common N/P/K/temperature/humidity/label aliases accepted).
- Similarity is not agronomic validation. Obtain locally verified crop requirement data before relying on planting decisions.
