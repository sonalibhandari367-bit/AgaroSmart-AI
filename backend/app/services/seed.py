"""Seed catalog metadata after migrations; run once per database deployment."""
from ..database import SessionLocal
from ..models import Crop, DatasetVersion
from .recommendation import load_catalog


def seed_catalog():
    with SessionLocal() as db:
        seed = load_catalog()
        version = "user-workbook-v1"
        for item in seed["crops"]:
            existing = db.query(Crop).filter_by(name=item["name"]).first()
            if existing is not None:
                existing.requirements = item["requirements"]
                existing.records = item["record_count"]
            else:
                db.add(Crop(name=item["name"], requirements=item["requirements"], provenance=seed["provenance"], source_version=version, records=item["record_count"]))
        if not db.query(DatasetVersion).filter_by(name="crop_observations", version=version).first():
            db.add(DatasetVersion(name="crop_observations", source_name=seed["source_file"], version=version, provenance=seed["provenance"], row_count=seed["source_records"], error_count=0, quality_report={"duplicates_removed":seed["duplicate_rows_removed"], "missing_values_imputed":0}))
        db.commit()
