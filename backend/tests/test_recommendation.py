import math
from statistics import mean, stdev

import pytest

from app.services.recommendation import PARAMETERS, load_catalog, rank_crops
from scripts.build_catalog import default_csv, percentile, read_rows


@pytest.fixture(scope="module")
def rows():
    return read_rows(default_csv())


@pytest.mark.parametrize("label", ["rice", "chickpea", "coffee", "cotton", "banana", "apple"])
def test_real_csv_row_ranks_first(rows, label):
    row = next(row for row in rows if row["label"] == label)
    assert rank_crops(row)[0]["crop"] == label


def test_rice_similarity_and_separation(rows):
    # Fixed second rice observation, not a synthetic crop-mean input.
    row = [row for row in rows if row["label"] == "rice"][1]
    results = rank_crops(row)
    assert results[0]["crop"] == "rice"
    assert results[0]["score"] >= 70
    assert results[0]["score"] - results[1]["score"] >= 20


def fixture_catalog(mean=5, std=2):
    return {"provenance": "test fixture only", "crops": [{
        "name": "test-crop", "record_count": 100,
        "requirements": {key: {"min": 0, "max": 10, "mean": mean,
                               "std": std, "p5": 2, "p95": 8} for key in PARAMETERS},
    }]}


def test_score_uses_distance_inside_observed_range():
    catalog = fixture_catalog()
    centered = rank_crops(dict.fromkeys(PARAMETERS, 5), catalog)[0]
    offset = rank_crops(dict.fromkeys(PARAMETERS, 7), catalog)[0]
    assert centered["score"] == 100
    assert offset["score"] == round(100 * math.exp(-0.5), 1)
    assert centered["status"] == "model_prediction_from_observed_ranges"


def test_scale_floor():
    result = rank_crops(dict.fromkeys(PARAMETERS, 105), fixture_catalog(mean=100, std=0))[0]
    assert result["score"] == round(100 * math.exp(-0.5), 1)


def test_percentile_status_and_count():
    values = dict.fromkeys(PARAMETERS, 5)
    values.update(nitrogen=1, phosphorus=9, potassium=2, rainfall_mm=8)
    result = rank_crops(values, fixture_catalog())[0]
    assert result["matched_parameters"] == 5
    evidence = {item["parameter"]: item for item in result["evidence"]}
    assert evidence["nitrogen"]["status"] == "low"
    assert evidence["phosphorus"]["status"] == "high"
    assert evidence["potassium"]["status"] == evidence["rainfall_mm"]["status"] == "ok"
    assert evidence["nitrogen"]["observed_min"] == 0
    assert evidence["nitrogen"]["ideal_min"] == 2
    assert evidence["nitrogen"]["ideal_max"] == 8


def test_context_does_not_affect_scores(rows):
    row = rows[0]
    assert rank_crops(row) == rank_crops(dict(row, soil_type="clay", location="Delhi", growing_season="winter"))
    assert len(rank_crops(row)) == 5


def test_catalog_statistics_match_csv(rows):
    for crop in load_catalog()["crops"]:
        for key, stats in crop["requirements"].items():
            values = [row[key] for row in rows if row["label"] == crop["name"]]
            assert stats["mean"] == pytest.approx(mean(values))
            assert stats["std"] == pytest.approx(stdev(values))
            assert stats["min"] == min(values)
            assert stats["max"] == max(values)
            assert stats["p5"] == pytest.approx(percentile(values, 0.05))
            assert stats["p95"] == pytest.approx(percentile(values, 0.95))
