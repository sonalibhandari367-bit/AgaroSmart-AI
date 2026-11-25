from starlette.testclient import TestClient
from app.main import app

def test_health_catalog_and_recommendation_persistence():
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status":"ok","database":"connected"}
        catalog = client.get("/api/crops").json()
        assert catalog["count"] == 22
        payload = {"nitrogen":80,"phosphorus":45,"potassium":40,"ph":6.5,"temperature_c":24,"humidity_pct":72,"rainfall_mm":100}
        response = client.post("/api/recommendations",json=payload)
        assert response.status_code == 200
        body=response.json()
        assert len(body["results"]) == 5
        assert body["recommendation_id"] > 0
        assert "not probabilities" in body["interpretation"]

def test_input_validation_and_admin_auth():
    with TestClient(app) as client:
        payload = {"nitrogen":-1,"phosphorus":45,"potassium":40,"ph":6.5,"temperature_c":24,"humidity_pct":72,"rainfall_mm":100}
        assert client.post("/api/recommendations",json=payload).status_code == 422
        assert client.post("/api/admin/imports").status_code == 401

def test_authenticated_import_versions_quality_report():
    csv = "nitrogen,phosphorus,potassium,temperature_c,humidity_pct,ph,rainfall_mm,crop\n1,2,3,20,60,6,50,rice\n".encode()
    with TestClient(app) as client:
        response=client.post("/api/admin/imports",headers={"X-Admin-Token":"test-admin-token"},files={"file":("sample.csv",csv,"text/csv")})
        assert response.status_code == 201
        assert response.json()["quality_report"]["accepted_rows"] == 1
