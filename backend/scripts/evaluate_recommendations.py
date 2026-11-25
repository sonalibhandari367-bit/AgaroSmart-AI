"""Evaluate all source rows against the catalog (in-sample, not held-out)."""
import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.recommendation import load_catalog, rank_crops
from scripts.build_catalog import default_csv, read_rows


def evaluate(csv_path: Path) -> None:
    rows = read_rows(csv_path)
    if not rows:
        raise ValueError("CSV contains no observations")
    catalog = load_catalog()
    top1 = top3 = 0
    confusions = Counter()
    for row in rows:
        predicted = [item["crop"] for item in rank_crops(row, catalog)]
        actual = row["label"]
        top1 += predicted[0] == actual
        top3 += actual in predicted[:3]
        if predicted[0] != actual:
            confusions[(actual, predicted[0])] += 1
    print(f"Rows: {len(rows)}; evaluation is in-sample (catalog built from this dataset).")
    print(f"Top-1 accuracy: {top1 / len(rows):.2%} ({top1}/{len(rows)})")
    print(f"Top-3 accuracy: {top3 / len(rows):.2%} ({top3}/{len(rows)})")
    print("5 most confused crop pairs (actual -> predicted; top-1 errors):")
    for (actual, predicted), count in sorted(confusions.items(), key=lambda item: (-item[1], item[0]))[:5]:
        print(f"  {actual} -> {predicted}: {count}")
    if not confusions:
        print("  None")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=default_csv())
    evaluate(parser.parse_args().csv)
