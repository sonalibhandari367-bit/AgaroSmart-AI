import hashlib
import io
import pandas as pd

REQUIRED = ["nitrogen", "phosphorus", "potassium", "temperature_c", "humidity_pct", "ph", "rainfall_mm", "crop"]
LIMITS = {"nitrogen":(0,200), "phosphorus":(0,200), "potassium":(0,250), "temperature_c":(-20,60), "humidity_pct":(0,100), "ph":(0,14), "rainfall_mm":(0,2000)}


def clean_csv(raw: bytes) -> tuple[pd.DataFrame, dict]:
    try:
        frame = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise ValueError(f"Could not parse CSV: {exc}") from exc
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    aliases = {"n":"nitrogen", "p":"phosphorus", "k":"potassium", "temperature":"temperature_c", "humidity":"humidity_pct", "label":"crop"}
    frame = frame.rename(columns={key:value for key,value in aliases.items() if key in frame.columns and value not in frame.columns})
    missing_columns = [column for column in REQUIRED if column not in frame.columns]
    if missing_columns:
        raise ValueError("Missing required columns: " + ", ".join(missing_columns))
    frame = frame[REQUIRED].copy()
    source_rows = len(frame)
    blank_rows = int(frame.isna().any(axis=1).sum())
    frame = frame.dropna(subset=REQUIRED)
    for column, (low, high) in LIMITS.items():
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    invalid_numeric = int(frame[[*LIMITS]].isna().any(axis=1).sum())
    frame = frame.dropna(subset=list(LIMITS))
    range_invalid = pd.Series(False, index=frame.index)
    for column, (low, high) in LIMITS.items():
        range_invalid |= ~frame[column].between(low, high)
    invalid_range = int(range_invalid.sum())
    frame = frame.loc[~range_invalid]
    frame["crop"] = frame["crop"].astype(str).str.strip().str.lower()
    frame = frame[frame["crop"].str.len().between(1, 100)]
    before_duplicates = len(frame)
    frame = frame.drop_duplicates()
    report = {"source_rows":source_rows, "accepted_rows":len(frame), "blank_rows_dropped":blank_rows, "invalid_numeric_rows_dropped":invalid_numeric, "out_of_range_rows_dropped":invalid_range, "duplicate_rows_dropped":before_duplicates-len(frame), "sha256":hashlib.sha256(raw).hexdigest(), "missing_values_imputed":0}
    return frame, report
