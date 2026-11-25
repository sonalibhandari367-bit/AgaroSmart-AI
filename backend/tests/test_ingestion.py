from app.services.ingestion import clean_csv

def test_csv_cleaning_reports_duplicates_blanks_and_range_errors():
    raw = b"N,P,K,temperature,humidity,ph,rainfall,label\n1,2,3,20,60,6,50,rice\n1,2,3,20,60,6,50,rice\n,,,,,,,\n1,2,3,20,60,20,50,maize\n"
    frame, report = clean_csv(raw)
    assert len(frame) == 1
    assert report["duplicate_rows_dropped"] == 1
    assert report["blank_rows_dropped"] == 1
    assert report["out_of_range_rows_dropped"] == 1
    assert report["missing_values_imputed"] == 0

def test_missing_required_column_fails():
    try:
        clean_csv(b"nitrogen,crop\n1,rice\n")
    except ValueError as exc:
        assert "Missing required columns" in str(exc)
    else:
        raise AssertionError("Expected required-column validation")
