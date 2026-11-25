"""Enrich the existing catalog without removing metadata or requirement fields."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FEATURE_COLUMNS = dict(zip(
    ("nitrogen", "phosphorus", "potassium", "temperature_c", "humidity_pct", "ph", "rainfall_mm"),
    ("N", "P", "K", "temperature", "humidity", "ph", "rainfall"),
))


def default_csv() -> Path:
    original = DATA_DIR / "Crop_recommendation.csv"
    return original if original.exists() else DATA_DIR / "crop_observations_user_provided.csv"


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return [dict(
            {key: float(row[key] if key in row else row[column])
             for key, column in FEATURE_COLUMNS.items()},
            label=row.get("label", row.get("crop", "")).strip(),
        ) for row in csv.DictReader(source)]


def percentile(values: list[float], fraction: float) -> float:
    """Linearly interpolate percentiles at (n - 1) * fraction."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def build_catalog(csv_path: Path, catalog_path: Path) -> dict:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    groups = defaultdict(list)
    for row in read_rows(csv_path):
        groups[row["label"]].append(row)
    if set(groups) != {crop["name"] for crop in catalog["crops"]}:
        raise ValueError("CSV crop labels must match the existing catalog")
    for crop in catalog["crops"]:
        for key in FEATURE_COLUMNS:
            values = [row[key] for row in groups[crop["name"]]]
            stats = {"mean": mean(values), "std": stdev(values) if len(values) > 1 else 0.0,
                     "p5": percentile(values, 0.05), "p95": percentile(values, 0.95),
                     "min": min(values), "max": max(values)}
            # Existing values are preserved; only missing statistics are added.
            for name, value in stats.items():
                crop["requirements"][key].setdefault(name, value)
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    return catalog


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=default_csv())
    parser.add_argument("--catalog", type=Path, default=DATA_DIR / "crop_catalog.json")
    args = parser.parse_args()
    result = build_catalog(args.csv, args.catalog)
    print(f"Enriched {len(result['crops'])} crops from {args.csv.name} (sample std; linear percentiles).")
