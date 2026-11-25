# API reference

Base URL: `http://localhost:8000/api`. Interactive OpenAPI docs are at `/docs`.

## `GET /health`
Returns `{ "status": "ok", "database": "connected" }` after a database query succeeds. Returns HTTP 503 if the query fails.

## `GET /crops`
Lists crop range summaries, source version, provenance, and explicit `unverified_user_dataset_observation` status.

## `POST /recommendations`
Requires JSON fields: `nitrogen` (0–200), `phosphorus` (0–200), `potassium` (0–250), `ph` (0–14), `temperature_c` (-20–60), `humidity_pct` (0–100), `rainfall_mm` (0–2000). Optional fields: `soil_type`, `location`, `growing_season`; optional `limit` is 1–22. Units are undocumented in the workbook; submitted values must use matching dataset conventions. Response includes ranked candidates, range evidence, score explanation, assumptions, unknowns, source provenance and persisted recommendation ID. Scores are similarity measures, never probability or suitability claims.

## `POST /admin/imports`
Multipart field `file`, CSV only, maximum size configured by `MAX_UPLOAD_BYTES`. Requires `X-Admin-Token` equal to the server-side `ADMIN_API_TOKEN`. Upload is parsed, validated, cleaned and versioned with a quality report. Missing required values are dropped, never imputed; invalid numeric/range rows and exact duplicate rows are reported. Uploads do not replace the active catalog.
