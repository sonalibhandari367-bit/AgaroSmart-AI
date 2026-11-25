import json
import math
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
        squared_z = []
        evidence = []
        for key in PARAMETERS:
            requirement = crop["requirements"][key]
            value = float(values[key])
            low, high = requirement["min"], requirement["max"]
            scale = max(requirement["std"], 0.05 * abs(requirement["mean"]))
            # A constant zero feature has no usable scale.
            z = (value - requirement["mean"]) / scale if scale else (0.0 if value == requirement["mean"] else math.inf)
            squared_z.append(z * z)
            ideal_min, ideal_max = requirement["p5"], requirement["p95"]
            status = "low" if value < ideal_min else "high" if value > ideal_max else "ok"
            evidence.append({"parameter": key, "label": LABELS[key], "value": value, "observed_min": low, "observed_max": high, "match": status == "ok", "status": status, "ideal_min": ideal_min, "ideal_max": ideal_max})
        distance = math.sqrt(sum(squared_z) / len(PARAMETERS))
        score = 100 * math.exp(-distance * distance / 2)
        matches = sum(item["match"] for item in evidence)
        candidates.append({"crop": crop["name"], "score": score, "matched_parameters": matches, "total_parameters": len(PARAMETERS), "evidence": evidence, "provenance": catalog["provenance"], "record_count": crop["record_count"], "status": "model_prediction_from_observed_ranges"})
    ranked = sorted(candidates, key=lambda item: (-item["score"], item["crop"]))[:limit]
    for item in ranked:
        item["score"] = round(item["score"], 1)
    return ranked
