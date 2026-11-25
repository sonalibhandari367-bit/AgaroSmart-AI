from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from .models import Crop, DatasetVersion, Recommendation, RecommendationDetail, SoilMeasurement, WeatherMeasurement
from .schemas import RecommendationRequest
from .services.ingestion import clean_csv
from .services.recommendation import load_catalog, rank_crops
from .services.seed import seed_catalog

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Hosted databases are migrated and seeded explicitly, never on cold starts.
    if not settings.vercel and engine is not None:
        Base.metadata.create_all(bind=engine)
        seed_catalog()
    yield



app = FastAPI(title="AgroSmart AI API", version="1.0.0", description="Transparent crop candidates ranked against user-provided observations. Predictions are not agronomic advice.", lifespan=lifespan, debug=False, docs_url=None if settings.vercel else "/docs", redoc_url=None if settings.vercel else "/redoc", openapi_url=None if settings.vercel else "/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Admin-Token"])


def admin_guard(x_admin_token: str | None = Header(default=None)):
    if not settings.admin_api_token or x_admin_token is None or not __import__("hmac").compare_digest(x_admin_token, settings.admin_api_token):
        raise HTTPException(status_code=401, detail="Valid administrator token required")


@app.get("/api/health")
def health(db: Session | None = Depends(get_db)):
    if db is None:
        return {"status":"ok", "database":"catalog_only"}
    try:
        db.execute(text("SELECT 1"))
        return {"status":"ok", "database":"connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@app.get("/api/crops")
def crops(db: Session | None = Depends(get_db)):
    if db is None:
        catalog = load_catalog()
        items = [{"name":c["name"], "requirements":c["requirements"], "provenance":catalog["provenance"], "source_version":"user-workbook-v1", "record_count":c["record_count"], "fact_status":"unverified_user_dataset_observation"} for c in sorted(catalog["crops"], key=lambda item: item["name"])]
        return {"items":items, "count":len(items)}
    return {"items":[{"name":c.name, "requirements":c.requirements, "provenance":c.provenance, "source_version":c.source_version, "record_count":c.records, "fact_status":"unverified_user_dataset_observation"} for c in db.query(Crop).order_by(Crop.name).all()], "count":db.query(Crop).count()}


@app.post("/api/recommendations")
def recommendations(request: RecommendationRequest, db: Session | None = Depends(get_db)):
    values = request.model_dump(exclude={"limit"})
    results = rank_crops(values, limit=request.limit)
    record_id = 0
    if db is not None:
        soil = SoilMeasurement(nitrogen=values["nitrogen"], phosphorus=values["phosphorus"], potassium=values["potassium"], ph=values["ph"], soil_type=values["soil_type"])
        weather = WeatherMeasurement(temperature_c=values["temperature_c"], humidity_pct=values["humidity_pct"], rainfall_mm=values["rainfall_mm"], location=values["location"], growing_season=values["growing_season"])
        db.add_all([soil, weather]); db.flush()
        version = db.query(DatasetVersion).filter_by(name="crop_observations").order_by(DatasetVersion.id.desc()).first()
        record = Recommendation(soil_measurement_id=soil.id, weather_measurement_id=weather.id, dataset_version_id=version.id if version else None)
        db.add(record); db.flush()
        for rank, result in enumerate(results, 1):
            db.add(RecommendationDetail(recommendation_id=record.id, crop_name=result["crop"], rank=rank, score=result["score"], explanation={"matched_parameters":result["matched_parameters"], "evidence":result["evidence"], "provenance":result["provenance"], "status":result["status"]}))
        db.commit()
        record_id = record.id
    return {"recommendation_id":record_id, "results":results, "method":"Gaussian similarity from RMS standardized distance to per-crop means; std floor is 5% of absolute mean; sorted by score", "interpretation":"Scores rank similarity to this dataset only. They are not probabilities, measured yields, verified agronomic requirements, or a guarantee of suitability.", "assumptions":["N/P/K units follow the supplied workbook convention and are not independently verified."], "unavailable_information":["location-specific climate and soil context", "soil type effect", "growing-season timing", "yield or economic outcomes"], "dataset_provenance":load_catalog()["provenance"]}


@app.post("/api/admin/imports", status_code=201)
async def import_csv(file: UploadFile = File(...), _: None = Depends(admin_guard), db: Session | None = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured for persistent imports")
    if file.content_type not in {"text/csv", "application/vnd.ms-excel", "application/csv"} or not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Upload a CSV file")
    raw = await file.read(settings.max_upload_bytes + 1)
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="CSV exceeds configured size limit")
    try:
        _, report = clean_csv(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    version = report["sha256"][:16]
    dataset = db.query(DatasetVersion).filter_by(name="csv_import", version=version).first()
    if dataset is None:
        dataset = DatasetVersion(name="csv_import", source_name=(file.filename or "upload.csv")[:255], version=version, provenance="Uploaded by authenticated administrator; source validity not independently verified.", row_count=report["accepted_rows"], error_count=report["source_rows"]-report["accepted_rows"], quality_report=report)
        db.add(dataset); db.commit(); db.refresh(dataset)
    return {"dataset_version_id":dataset.id, "version":dataset.version, "quality_report":report, "note":"Import is validated and versioned. It does not replace the active crop catalog automatically."}
