import json
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "crop_catalog.json"
PARAMETERS = ("nitrogen", "phosphorus", "potassium", "temperature_c", "humidity_pct", "ph", "rainfall_mm")
LABELS = {"nitrogen":"Nitrogen", "phosphorus":"Phosphorus", "potassium":"Potassium", "temperature_c":"Temperature", "humidity_pct":"Humidity", "ph":"Soil pH", "rainfall_mm":"Rainfall"}


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def rank_crops(values: dict[str, Any], catalog: dict[str, Any] | None = None, limit: int = 5) -> list[dict[str, Any]]:
    catalog = catalog or load_catalog()
    candidates = []
    for crop in catalog["crops"]:
        distance = 0.0
        evidence = []
        for key in PARAMETERS:
            requirement = crop["requirements"][key]
            value = float(values[key])
            low, high = requirement["min"], requirement["max"]
            width = max(high - low, max(abs(requirement["mean"]), 1.0) * 0.05)
            gap = max(low - value, value - high, 0.0)
            distance += gap / width
            evidence.append({"parameter": key, "label": LABELS[key], "value": value, "observed_min": low, "observed_max": high, "match": gap == 0})
        score = round(100 / (1 + distance), 1)
        matches = sum(item["match"] for item in evidence)
        candidates.append({"crop": crop["name"], "score": score, "matched_parameters": matches, "total_parameters": len(PARAMETERS), "evidence": evidence, "provenance": catalog["provenance"], "record_count": crop["record_count"], "status": "model_prediction_from_observed_ranges"})
    return sorted(candidates, key=lambda item: (-item["score"], item["crop"]))[:limit]
